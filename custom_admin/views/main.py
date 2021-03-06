from django.views.generic.edit import FormMixin, FormView
from django.views.generic import ListView
from django.http import Http404
from django.utils.decorators import method_decorator

from app.decorators import ajax_form_validate
from app.base import AjaxDisptcherProcessorMixin
from app.utils import MailSupportMixin
from experiences.models import Booking, Experience, NewProduct, CustomItinerary
from experiences.utils import *
from custom_admin.views.base import BookingInfoMixin
from custom_admin.forms import BookingForm, ExperienceUploadForm, CreateExperienceForm
from custom_admin.views.base import StatusGenerator
from custom_admin.mail import MailService
from Tripalocal_V1 import settings
from experiences.constant import ItineraryStatus
from import_from_partners.utils import PARTNER_IDS

import pytz
from datetime import *
from django.db.models import Q

class AdminCommonOperation(object):

    @method_decorator(ajax_form_validate(form_class=BookingForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=Booking, **kwargs)

    def _manipulate_multi_change_statuses(self, request, booking_list, **kwargs):
        booking_list= list(booking_list)
        for booking in booking_list:
            booking.change_status(new_status=kwargs['form'].cleaned_data['status'])
        return {'id':[booking.id for booking in booking_list]}

class ItineraryView(AjaxDisptcherProcessorMixin, FormMixin, ListView):
    model = CustomItinerary
    template_name = 'custom_admin/itineraries.html'
    context_object_name = 'itinerary_list'
    paginate_by = None

    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=CustomItinerary, **kwargs)

    def get_queryset(self):
        return self.model.objects.exclude(status="deleted").order_by('-submitted_datetime')

    def get_context_data(self, **kwargs):
        context = super(ItineraryView, self).get_context_data(**kwargs)
        conversion_cny = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/currency_conversion_rate/CNY.yaml').replace('\\', '/'))
        conversion_aud = load_config(os.path.join(settings.PROJECT_ROOT, 'experiences/currency_conversion_rate/AUD.yaml').replace('\\', '/'))
        for ci in context['itinerary_list']:
            guest_number_tuple = ci.get_guest_number()
            ci.guest_number = guest_number_tuple[0]
            ci.adult_number = guest_number_tuple[1]
            ci.child_number = guest_number_tuple[2]
            ci.price_aud = ci.get_price('aud', **{"conversion_aud":conversion_aud,"conversion_cny":conversion_cny})
            ci.price_cny = ci.get_price('cny', **{"conversion_aud":conversion_aud,"conversion_cny":conversion_cny})
            if ci.status != "paid":
                if pytz.timezone("UTC").localize(datetime.utcnow()) > timedelta(days=7) + ci.submitted_datetime:
                    ci.status = "Full price"
                else:
                    ci.status = "Discount price"
        return context

    def _manipulate_multi_change_statuses(self, request, itinerary_list, **kwargs):
        itinerary_list= list(itinerary_list)
        for itinerary in itinerary_list:
            if request.POST['status'] in ItineraryStatus.Allowed_Status:
                itinerary.change_status(new_status=request.POST['status'])
            else:
                raise ValueError("Invalid status")
        return {'id':[itinerary.id for itinerary in itinerary_list]}

    def _manipulate_duplicate_itineraries(self, request, itinerary_list, **kwargs):
        itinerary_list= list(itinerary_list)
        result_list = []
        for itinerary in itinerary_list:
            ci = itinerary.duplicate()
            ci.guest_number = ci.get_guest_number()
            ci.price_aud = ci.get_price('aud')
            ci.price_cny = ci.get_price('cny')
            if ci.status != "paid":
                if pytz.timezone("UTC").localize(datetime.utcnow()) > timedelta(days=7) + ci.submitted_datetime:
                    ci.status = "Full price"
                else:
                    ci.status = "Discount price"
            result_list.append({"id":ci.id, "guest_number":ci.guest_number,
                                "price_aud":ci.price_aud, "price_cny":ci.price_cny,
                                "status":ci.status, "title":ci.title})
        return {'itineraries':result_list}

class ExperienceView(AjaxDisptcherProcessorMixin, FormMixin, ListView):
    model = Experience
    template_name = 'custom_admin/experiences.html'
    context_object_name = 'experience_list'
    paginate_by = None

    def get_context_data(self, **kwargs):
        context = super(ExperienceView, self).get_context_data(**kwargs)
        for exp in context['experience_list']:
            exp_information = exp.get_information(settings.LANGUAGES[0][0])
            exp.title = exp_information.title
            exp.description = exp_information.description
            exp.activity = exp_information.activity
            exp.dress = exp_information.dress
            exp.interaction = exp_information.interaction
            exp.meetup_spot = exp_information.meetup_spot
            exp.dropoff_spot = exp_information.dropoff_spot
        return context

    @method_decorator(ajax_form_validate(form_class=ExperienceUploadForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=Experience, **kwargs)

    def _manipulate_post_status(self, request, experience, **kwargs):
        experience.change_status(kwargs['form'].cleaned_data['status'])

    def _manipulate_post_commission(self, request, experience, **kwargs):
        experience.update_commission(kwargs['form'].cleaned_data['commission'])
        return {'commission': kwargs['form'].cleaned_data['commission']}

class NewProductView(AjaxDisptcherProcessorMixin, FormMixin, ListView):
    model = NewProduct
    template_name = 'custom_admin/newproduct.html'
    context_object_name = 'newproduct_list'
    paginate_by = None

    def get_queryset(self):
        return self.model.objects.filter(Q(partner__isnull=True) | Q(partner__exact='')).exclude(type__in=["Flight", "Transfer", "Accommodation", "Restaurant", "Suggestion", "Pricing"])

    def get_context_data(self, **kwargs):
        context = super(NewProductView, self).get_context_data(**kwargs)
        for exp in context['newproduct_list']:
            exp.title = exp.get_information(settings.LANGUAGES[0][0]).title
            exp.host = exp.get_host()
        return context

    @method_decorator(ajax_form_validate(form_class=ExperienceUploadForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=NewProduct, **kwargs)

    def _manipulate_post_status(self, request, experience, **kwargs):
        experience.change_status(kwargs['form'].cleaned_data['status'])

    def _manipulate_post_commission(self, request, experience, **kwargs):
        experience.update_commission(kwargs['form'].cleaned_data['commission'])
        return {'commission': kwargs['form'].cleaned_data['commission']}

class PartnerProductView(AjaxDisptcherProcessorMixin, FormMixin, ListView):
    model = NewProduct
    template_name = 'custom_admin/partnerproduct.html'
    context_object_name = 'partnerproduct_list'
    paginate_by = None
    partner = ""

    def get_queryset(self):
        return self.model.objects.filter(partner=self.partner).order_by('status','id')

    def get_context_data(self, **kwargs):
        context = super(PartnerProductView, self).get_context_data(**kwargs)
        context['partnerproduct_list'] = list(context['partnerproduct_list'])
        price_updated = [e for e in context['partnerproduct_list'] if e.price > 0.0]
        price_not_updated = [e for e in context['partnerproduct_list'] if e.price == 0.0]

        new_index=0
        for exp in price_updated:
            exp.title_en = exp.get_information("en").title
            exp.title_cn = exp.get_information("cn").title
            exp.host = exp.get_host()

            #rtp_min = 10000000
            #rtp_max = 0
            sale_min = 10000000
            sale_max = 0
            for og in exp.optiongroup_set.all():
                for oi in og.optionitem_set.all():
                    #if oi.retail_price < rtp_min:
                    #    rtp_min = oi.retail_price
                    #elif oi.retail_price > rtp_max:
                    #    rtp_max = oi.retail_price
                    if oi.price < sale_min:
                        sale_min = oi.price
                    elif oi.price > sale_max:
                        sale_max = oi.price
            #if rtp_min > rtp_max:
            #    rtp_min = rtp_max
            if sale_min > sale_max:
                sale_min = sale_max
            #exp.rtp = (rtp_min, rtp_max)
            exp.sale = (round(sale_min,2), round(sale_max,2))
            if not isEnglish(exp.title_cn):
                old_index = price_updated.index(exp)
                price_updated.insert(new_index, price_updated.pop(old_index))
                new_index += 1
        context['partnerproduct_list'] = price_updated + price_not_updated
        return context

    @method_decorator(ajax_form_validate(form_class=ExperienceUploadForm))
    def post(self, request, **kwargs):
        return self._process_request_with_general_return(request, model_class=NewProduct, **kwargs)

    def _manipulate_post_status(self, request, experience, **kwargs):
        experience.change_status(kwargs['form'].cleaned_data['status'])

    def _manipulate_post_commission(self, request, experience, **kwargs):
        experience.update_commission(kwargs['form'].cleaned_data['commission'])
        return {'commission': kwargs['form'].cleaned_data['commission']}

class ExperienceozProductView(PartnerProductView):
    partner = PARTNER_IDS.get("experienceoz")

class RezdyProductView(PartnerProductView):
    partner = PARTNER_IDS.get("rezdy")

class BookingView(AjaxDisptcherProcessorMixin, BookingInfoMixin, MailSupportMixin, AdminCommonOperation, ListView):
    model = Booking
    template_name = 'custom_admin/bookings.html'
    form_class = BookingForm
    context_object_name = 'booking_list'
    paginate_by = None

    def get_queryset(self):
        return self.model.objects.exclude(status__iexact="draft")

    def get_context_data(self, **kwargs):
        context = super(BookingView, self).get_context_data(**kwargs)
        context['form'] = self.form_class()
        return context

    def _manipulate_upload_review(self, request, booking, **kwargs):
        booking.upload_review(rate=kwargs['form'].cleaned_data['rate'], review=kwargs['form'].cleaned_data['review'])
        booking_list = [booking]
        status_generator = StatusGenerator(booking_list)
        status_generator.generate_status_description()
        return {'status_description': booking_list[0].status_description, 'id':booking_list[0].id, 'colour':booking_list[0].colour, 'actions': booking_list[0].actions}

    def _manipulate_change_time(self, request, booking, **kwargs):
        new_datetime = booking.change_time(new_date=kwargs['form'].cleaned_data['new_date'], new_time=kwargs['form'].cleaned_data['new_time'])
        return {'new_datetime': new_datetime.strftime("%d %b %Y %H:%M"), 'id':booking.id}

    def _manipulate_change_status(self, request, booking, **kwargs):
        new_status = booking.change_status(new_status=kwargs['form'].cleaned_data['status'])
        booking_list = [booking]
        status_generator = StatusGenerator(booking_list)
        status_generator.generate_status_description()
        return {'status_description': booking_list[0].status_description, 'new_status': new_status, 'id':booking.id, 'actions': booking_list[0].actions}

    def _manipulate_send_mail(self, request, booking_list, **kwargs):
        recipient = request.POST['recipient']
        booking_list = list(booking_list)
        mail_service = MailService()
        for booking in booking_list:
            booking_status = booking.status
            mail_service.set_mail_info(booking)
            send_mail = None
            if recipient == 'host':
                if booking_status == 'requested' or booking_status == 'paid':
                    mail_service.send_notification_email_to_host()
                elif booking_status == 'accepted':
                    mail_service.send_confirmation_email_to_host()
            elif recipient == 'guest':
                if booking_status == 'requested' or booking_status == 'paid':
                    mail_service.send_notification_email_to_guest()
                elif booking_status == 'accepted':
                    mail_service.send_confirmation_email_to_guest()
            else:
                raise Http404('Wrong request parameter.')

class BookingArchiveView(AjaxDisptcherProcessorMixin, BookingInfoMixin, AdminCommonOperation, ListView):
    model = Booking
    template_name = 'custom_admin/booking-archives.html'
    form_class = BookingForm
    context_object_name = 'booking_list'
    paginate_by = None

    def get_queryset(self):
        return self.model.objects.exclude(status__iexact="draft")

class PaymentView(BookingInfoMixin, ListView):
    model = Booking
    template_name = 'custom_admin/payment.html'
    context_object_name = 'booking_list'
    paginate_by = None

    def get_context_data(self, **kwargs):
        # Call the base implementation first to get a context
        context = super(PaymentView, self).get_context_data(**kwargs)
        for booking in context['booking_list']:
            booking.attach_guest_price()
        return context
