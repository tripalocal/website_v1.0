﻿import traceback

from django.http import Http404
from django.db import models
from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User
from datetime import datetime
from django.utils import timezone
from allauth.socialaccount.models import SocialAccount
from Tripalocal_V1 import settings
from polymorphic import PolymorphicModel


class ExperienceTag(models.Model):
    tag = models.CharField(max_length=100)
    language = models.CharField(max_length=2)

class WechatProduct(models.Model):
    title = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=6, decimal_places=2)
    valid = models.BooleanField(default=False)

    def __str__(self):
        return self.title

class WechatBooking(models.Model):
    product = models.ForeignKey(WechatProduct)
    datetime = models.DateTimeField(default=timezone.now, blank=True)
    trade_no = models.CharField(max_length=64)
    phone_num = models.CharField(max_length=15, default='')
    email = models.CharField(max_length=25, default='')
    paid = models.BooleanField(default=False)

    def __str__(self):
        return self.trade_no

class Provider(models.Model):
    user = models.OneToOneField(User, null=True)
    company = models.CharField(max_length=100)
    website = models.CharField(max_length=50, blank=True)
    email = models.CharField(max_length=30, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)

    def __str__(self):
        return self.company

class Product(models.Model):
    NORMAL = 'NORMAL'
    AGE_PRICE = 'AGE'
    DYNAMIC = 'DYNAMIC'

    PRICE_CHOICES = (
        (NORMAL, 'Normal price per person'),
        (AGE_PRICE, 'Price for different age group'),
        (DYNAMIC, 'Dynamic price'),
    )

    provider = models.ForeignKey(Provider)
    price_type = models.CharField(max_length=6, choices=PRICE_CHOICES, default=NORMAL,
                                  help_text="Only one of the price type will take effact.")
    normal_price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    dynamic_price = models.CharField(max_length=100, blank=True)
    adult_price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    children_price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    adult_age = models.IntegerField(blank=True, null=True, help_text="Above what age should pay adult price.")

    duration_in_min = models.IntegerField(blank=True, null=True, help_text="How long will it be in minutes?")
    min_group_size = models.IntegerField(blank=True, null=True)
    book_in_advance = models.IntegerField(blank=True, null=True)
    instant_booking = models.TextField(blank=True)
    free_translation = models.BooleanField(default=False)
    order_on_holiday = models.BooleanField(default=False, help_text="If supplier take order during weekend and holiday "
                                                                    "particularly instant order during holiday")

    def __str__(self):
        t = self.get_product_title(settings.LANGUAGES[0][0])
        return str(self.id) + '--' + t

    def get_product_title(self, lang):
        if self.producti18n_set is not None and len(self.producti18n_set.all()) > 0:
            t = self.producti18n_set.filter(language=lang)
            if len(t)>0:
                return t[0].title
            else:
                return self.producti18n_set.all()[0].title
        else:
            return ''

class ProductI18n(models.Model):
    EN = 'en'
    ZH = 'zh'

    LANG_CHOICES = (
        (EN, 'English'),
        (ZH, '中文'),
    )

    language = models.CharField(max_length=3, choices=LANG_CHOICES, default=EN)
    product = models.ForeignKey(Product)
    title = models.CharField(max_length=100)
    location = models.TextField(blank=True)
    background_info = models.TextField(blank=True)
    description = models.TextField(blank=True)
    service = models.TextField(blank=True)
    highlights = models.TextField(blank=True)
    schedule = models.TextField(blank=True)
    ticket_use_instruction = models.TextField(blank=True)
    refund_policy = models.TextField(blank=True)
    notice = models.TextField(blank=True)
    tips = models.TextField(blank=True)
    whats_included = models.TextField(blank=True,
                                      help_text="What's included in the price (pickup/meal/drink/certificate/photo)")
    pickup_detail = models.TextField(blank=True)
    combination_options = models.TextField(blank=True,
                                           help_text="Combination option (for example the client can tick to choose "
                                                     "whether to add translator or driver into the tour, and we can "
                                                     "set standard price for different durations of such service "
                                                     "provided)")
    insurance = models.TextField(blank=True)
    disclaimer = models.TextField(blank=True)

    def __str__(self):
        return self.title

class AbstractExperience(PolymorphicModel):
    pass

class Experience(AbstractExperience):
    type = models.CharField(max_length=50)
    language = models.CharField(max_length=50)

    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    allow_instant_booking = models.BooleanField(default=False)
    duration = models.FloatField()

    guest_number_max = models.IntegerField()
    guest_number_min = models.IntegerField()
    price = models.DecimalField(max_digits=6, decimal_places=2)
    currency = models.CharField(max_length=10)
    dynamic_price = models.CharField(max_length=100)

    #title = models.CharField(max_length=100)
    #description = models.TextField()
    #activity = models.TextField()
    #interaction = models.TextField()
    #dress = models.TextField()
    
    city = models.CharField(max_length=50)
    address = models.TextField()
    #meetup_spot = models.TextField()
    
    hosts = models.ManyToManyField(User, related_name='experience_hosts')
    guests = models.ManyToManyField(User, related_name='experience_guests')
    status = models.CharField(max_length=50)

    tags = models.ManyToManyField(ExperienceTag, related_name='experience_tags')
    commission = models.FloatField(default=0.3)

    def __str__(self):
        t = get_experience_title(self, settings.LANGUAGES[0][0])
        if t is None:
            t = ''
        s = self.status if self.status != None else ''
        c = self.city if self.city != None else ''
        return str(self.id) + '--' + t + '--' + s + '--' + c

    def get_experience_i18n_info(self, **kwargs):
        # The default language is english.
        language = 'en'
        if 'language' in kwargs:
            language = kwargs['language']
        self.title = get_experience_title(self, language)
        self.description = get_experience_description(self, language)
        self.activity = get_experience_activity(self, language)
        self.dress = get_experience_dress(self, language)
        self.interaction = get_experience_interaction(self, language)
        self.meetup_spot = get_experience_meetup_spot(self, language)
        self.dropoff_spot = get_experience_dropoff_spot(self, language)

        #exp = ExperienceI18n.objects.filter(experience_id=self.id, language=language)
        #if exp.__len__() == 1:
            # exp_i18n = exp[0]
            # self.title = exp_i18n.title
            # self.description = exp_i18n.description
            # self.activity = exp_i18n.activity
            # self.dress = exp_i18n.activity
            # self.interaction = exp_i18n.interaction
            # self.meetup_spot = exp_i18n.meetup_spot
            # self.dropoff_spot = exp_i18n.dropoff_spot

    def new_experience_i18n_info(self, **kwargs):
        self._new_experience_i18n_info('zh')
        self._new_experience_i18n_info('en')


    def _new_experience_i18n_info(self, language, **kwargs):
        ExperienceTitle.objects.create(experience=self, language=language)
        ExperienceDescription.objects.create(experience=self, language=language)
        ExperienceActivity.objects.create(experience=self, language=language)
        ExperienceDress.objects.create(experience=self, language=language)
        ExperienceInteraction.objects.create(experience=self, language=language)
        ExperienceMeetupSpot.objects.create(experience=self, language=language)
        ExperienceDropoffSpot.objects.create(experience=self, language=language)

    def change_status(self, new_status=None):
        self.status = new_status
        self.save()

    def update_commission(self, commission):
        self.commission = commission
        self.save()

    class Meta:
        ordering = ['id']

class ExperienceI18n(models.Model):
    title = models.CharField(max_length=100, null=True)
    description = models.TextField(null=True)
    language = models.CharField(max_length=2, null=True)
    activity = models.TextField(null=True)
    interaction = models.TextField(null=True)
    dress = models.TextField(null=True)
    meetup_spot = models.TextField(null=True)
    dropoff_spot = models.TextField(null=True)
    experience = models.ForeignKey(Experience)

class NewProduct(AbstractExperience):
    NORMAL = 'NORMAL'
    AGE_PRICE = 'AGE'
    DYNAMIC = 'DYNAMIC'

    PRICE_CHOICES = (
        (NORMAL, 'Normal price per person'),
        (AGE_PRICE, 'Price for different age group'),
        (DYNAMIC, 'Dynamic price'),
    )

    LISTED = 'Listed'
    UNLISTED = 'Unlisted'

    STATUS_CHOICES = (
        (LISTED, 'Listed'),
        (UNLISTED, 'Unlisted'),
    )

    start_datetime = models.DateTimeField(null=True)
    end_datetime = models.DateTimeField(null=True)
    provider = models.ForeignKey(Provider)
    city = models.CharField(max_length=50)
    language = models.CharField(max_length=50, default="english")
    currency = models.CharField(max_length=10, default="aud")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=UNLISTED)
    price_type = models.CharField(max_length=6, choices=PRICE_CHOICES, default=NORMAL,
                                  help_text="Only one of the price type will take effact.")
    price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    commission = models.FloatField(default=0.3)
    dynamic_price = models.CharField(max_length=100, blank=True)
    adult_price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    children_price = models.DecimalField(max_digits=6, decimal_places=2, blank=True, null=True)
    adult_age = models.IntegerField(blank=True, null=True, help_text="Above what age should pay adult price.")
    duration = models.FloatField(blank=True, null=True, help_text="How long will it be in hours?")
    guest_number_min = models.IntegerField(blank=True, null=True)
    guest_number_max = models.IntegerField(blank=True, null=True)
    book_in_advance = models.IntegerField(blank=True, null=True)
    instant_booking = models.TextField(blank=True)
    free_translation = models.BooleanField(default=False)
    order_on_holiday = models.BooleanField(default=False, help_text="If supplier take order during weekend and holiday "
                                                                    "particularly instant order during holiday")
    tags = models.ManyToManyField(ExperienceTag, related_name='newproduct_tags')

    def __str__(self):
        t = self.get_product_title(settings.LANGUAGES[0][0])
        return str(self.id) + '--' + t

    def get_product_title(self, lang):
        if self.newproducti18n_set is not None and len(self.newproducti18n_set.all()) > 0:
            t = self.newproducti18n_set.filter(language=lang)
            if len(t)>0:
                return t[0].title
            else:
                return self.newproducti18n_set.all()[0].title
        else:
            return ''

    def get_product_description(self, language):
        if self.newproducti18n_set is not None and len(self.newproducti18n_set.all()) > 0:
            t = self.newproducti18n_set.filter(language=language)
            if len(t)>0:
                return t[0].description
            else:
                return self.newproducti18n_set.all()[0].description
        else:
            return None

class NewProductI18n(models.Model):
    EN = 'en'
    ZH = 'zh'

    LANG_CHOICES = (
        (EN, 'English'),
        (ZH, '中文'),
    )

    language = models.CharField(max_length=3, choices=LANG_CHOICES, default=EN)
    product = models.ForeignKey(NewProduct)
    title = models.CharField(max_length=100)
    location = models.TextField(blank=True)
    background_info = models.TextField(blank=True)
    description = models.TextField(blank=True)
    service = models.TextField(blank=True)
    highlights = models.TextField(blank=True)
    schedule = models.TextField(blank=True)
    ticket_use_instruction = models.TextField(blank=True)
    refund_policy = models.TextField(blank=True)
    notice = models.TextField(blank=True)
    tips = models.TextField(blank=True)
    whatsincluded = models.TextField(blank=True,
                                      help_text="What's included in the price (pickup/meal/drink/certificate/photo)")
    pickup_detail = models.TextField(blank=True)
    combination_options = models.TextField(blank=True,
                                           help_text="Combination option (for example the client can tick to choose "
                                                     "whether to add translator or driver into the tour, and we can "
                                                     "set standard price for different durations of such service "
                                                     "provided)")
    insurance = models.TextField(blank=True)
    disclaimer = models.TextField(blank=True)

    def __str__(self):
        return self.title

class ExperienceTitle(models.Model):
    title = models.CharField(max_length=100)
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceDescription(models.Model):
    description = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceActivity(models.Model):
    activity = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceInteraction(models.Model):
    interaction = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceDress(models.Model):
    dress = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceMeetupSpot(models.Model):
    meetup_spot = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class ExperienceDropoffSpot(models.Model):
    dropoff_spot = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class InstantBookingTimePeriod(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat_end_date = models.DateField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    experience = models.ForeignKey(AbstractExperience)

class BlockOutTimePeriod(models.Model):
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    repeat_end_date = models.DateField()
    repeat = models.BooleanField(default=False)
    repeat_cycle = models.CharField(max_length=50)
    repeat_frequency = models.IntegerField()
    repeat_extra_information = models.CharField(max_length=50)
    experience = models.ForeignKey(AbstractExperience)

class WhatsIncluded(models.Model):
    item = models.CharField(max_length=50)
    included = models.BooleanField(default=False)
    details = models.TextField()
    language = models.CharField(max_length=2)
    experience = models.ForeignKey(Experience)

class Photo(models.Model):
    def upload_path(self, name):
        return self.directory + self.name

    name = models.CharField(max_length=50)
    directory = models.CharField(max_length=50)
    image = models.ImageField(upload_to=upload_path)
    experience = models.ForeignKey(AbstractExperience)

class ProductPhoto(models.Model):
    def upload_path(self, name):
        return 'products/{0}/{1}.jpg'.format(str(self.product.id), self.name)

    name = models.CharField(max_length=50, blank=False)
    image = models.ImageField(upload_to=upload_path)
    product = models.ForeignKey(Product, related_name='photos')

class Review(models.Model):
    user = models.ForeignKey(User)
    experience = models.ForeignKey(AbstractExperience)
    comment = models.TextField()
    rate = models.IntegerField()
    datetime = models.DateTimeField()
    personal_comment = models.TextField()
    operator_comment = models.TextField()

    def __str__(self):
        return self.user.email + "--" + get_experience_title(self.experience,settings.LANGUAGES[0][0])

class Coupon(models.Model):
    promo_code = models.CharField(max_length=10)
    start_datetime = models.DateTimeField()
    end_datetime = models.DateTimeField()
    rules = models.TextField()
    title = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.promo_code

class Booking(models.Model):
    user = models.ForeignKey(User)
    coupon = models.ForeignKey(Coupon)
    coupon_extra_information = models.TextField()
    guest_number = models.IntegerField()
    experience = models.ForeignKey(AbstractExperience)
    datetime = models.DateTimeField()
    status = models.CharField(max_length=50)
    submitted_datetime = models.DateTimeField()
    payment = models.ForeignKey("Payment", related_name="payment")
    refund_id = models.CharField(max_length=50)
    booking_extra_information = models.TextField()

    def __str__(self):
        return self.user.email + "--" + get_experience_title(self.experience,settings.LANGUAGES[0][0])

    def upload_review(self, rate=None, review=None):
        experience_id = self.experience_id
        user_id = self.user_id
        Review.objects.update_or_create(experience_id = int(experience_id), user_id = int(user_id), defaults = {'comment': review, 'rate': int(rate), 'datetime': datetime.now()})
        return True

    def change_time(self, new_time=None, new_date=None):
        if new_time and new_date:
            new_datetime = datetime.combine(new_date, new_time)
            self.datetime = new_datetime
            self.save()
            return new_datetime
        else:
            traceback.print_exc()
            raise Http404('Change time failed.')

    def change_status(self, new_status=None):
        if new_status == "archived":
            self.status = self.status + '_archived'
        elif new_status == "unarchived":
            self.status = self.status[:-9]
        else:
            self.status = new_status
        self.save()
        return self.status

    def get_experience(self):
        return get_object_or_404(Experience, id = self.experience_id)

    def get_guest(self):
        return get_object_or_404(User, id = self.user_id)

    def get_hosts(self):
        return self.get_experience().hosts.all()

    def attach_guest_price(self):
        host_price = float(self.experience.price) * float(self.guest_number)
        full_price = self._calculate_full_price(host_price)
        self.full_price = full_price
        self.host_price = host_price

    def _calculate_full_price(self, price):
        if type(price)==int or type(price) == float:
            if self.experience.commission is not None and self.experience.commission > 0:
                COMMISSION_PERCENT = round(self.experience.commission/(1-self.experience.commission),3)
            else:
                COMMISSION_PERCENT = settings.COMMISSION_PERCENT
            return round(price*(1.00+COMMISSION_PERCENT)*(1.00+settings.STRIPE_PRICE_PERCENT) + settings.STRIPE_PRICE_FIXED,2)

class Payment(models.Model):
    def __init__(self, *args, **kwargs):
        super(Payment, self).__init__(*args, **kwargs)
 
        # bring in stripe, and get the api key from settings.py
        import stripe
        stripe.api_key = settings.STRIPE_SECRET_KEY
 
        self.stripe = stripe
 
    # store the stripe charge id for this sale
    charge_id = models.CharField(max_length=32)
    booking = models.ForeignKey(Booking, related_name="booking")
    street1 = models.CharField(max_length=50)
    street2 = models.CharField(max_length=50)
    city = models.CharField(max_length=20)
    zip_code = models.CharField(max_length=4)
    state = models.CharField(max_length=3)
    country = models.CharField(max_length=15)
    phone_number = models.CharField(max_length=15)
 
    # you could also store other information about the sale
    # but I'll leave that to you!
 
    def charge(self, price_in_cents, currency, number=None, exp_month=None, exp_year=None, cvc=None, stripe_token=None):
        """
        Takes a the price and credit card details: number, currency, exp_month,
        exp_year, cvc.
 
        Returns a tuple: (Boolean, Class) where the boolean is if
        the charge was successful, and the class is response (or error)
        instance.
        """
 
        if self.charge_id: # don't let this be charged twice!
            return False, Exception(message="Already charged.")
 
        try:
            if stripe_token is not None:
                response = self.stripe.Charge.create(
                            amount = price_in_cents,
                            currency = currency.lower(),
                            source = stripe_token,
                            description='')
            else:
                response = self.stripe.Charge.create(
                            amount = price_in_cents,
                            currency = currency.lower(),
                            card = {
                                "number" : number,
                                "exp_month" : exp_month,
                                "exp_year" : exp_year,
                                "cvc" : cvc,
 
                                #### it is recommended to include the address!
                                "address_line1" : self.street1,
                                "address_line2" : self.street2,
                                "address_city" : self.city,
                                "address_zip" : self.zip_code,
                                "address_state" : self.state,
                                "address_country" : self.country,
                            },
                            description='')
 
            self.charge_id = response.id
 
        except self.stripe.CardError as ce:
            # charge failed
            return False, ce
        except Exception as ex:
            return False, ex
 
        return True, response

    def refund(self, charge_id, amount):
        try:
            ch = self.stripe.Charge.retrieve(charge_id)
            if amount != None:
                re = ch.refund(amount = amount) # ch.refunds.create() 
            else:
                re = ch.refund() # ch.refunds.create() 
            booking = Booking.objects.get(payment_id = Payment.objects.get(charge_id = ch.id).id)
            booking.status = "rejected"
            booking.refund_id = re.id
            booking.save()
        except self.stripe.error.StripeError as e:
            return False, e
        except Exception as e:
            return False, e
        return True, re

def get_experience_title(experience, language):
    if experience.experiencetitle_set is not None and len(experience.experiencetitle_set.all()) > 0:
        t = experience.experiencetitle_set.filter(language=language)
        if len(t)>0:
            return t[0].title
        else:
            return experience.experiencetitle_set.all()[0].title
    else:
        return None

def get_experience_activity(experience, language):
    if experience.experienceactivity_set is not None and len(experience.experienceactivity_set.all()) > 0:
        t = experience.experienceactivity_set.filter(language=language)
        if len(t)>0:
            return t[0].activity
        else:
            return experience.experienceactivity_set.all()[0].activity
    else:
        return None

def get_experience_description(experience, language):
    if experience.experiencedescription_set is not None and len(experience.experiencedescription_set.all()) > 0:
        t = experience.experiencedescription_set.filter(language=language)
        if len(t)>0:
            return t[0].description
        else:
            return experience.experiencedescription_set.all()[0].description
    else:
        return None

def get_experience_interaction(experience, language):
    if experience.experienceinteraction_set is not None and len(experience.experienceinteraction_set.all()) > 0:
        t = experience.experienceinteraction_set.filter(language=language)
        if len(t)>0:
            return t[0].interaction
        else:
            return experience.experienceinteraction_set.all()[0].interaction
    else:
        return None

def get_experience_dress(experience, language):
    if experience.experiencedress_set is not None and len(experience.experiencedress_set.all()) > 0:
        t = experience.experiencedress_set.filter(language=language)
        if len(t)>0:
            return t[0].dress
        else:
            return experience.experiencedress_set.all()[0].dress
    else:
        return None

def get_experience_meetup_spot(experience, language):
    if experience.experiencemeetupspot_set is not None and len(experience.experiencemeetupspot_set.all()) > 0:
        t = experience.experiencemeetupspot_set.filter(language=language)
        if len(t)>0:
            return t[0].meetup_spot
        else:
            return experience.experiencemeetupspot_set.all()[0].meetup_spot
    else:
        return None

def get_experience_dropoff_spot(experience, language):
    if experience.experiencedropoffspot_set is not None and len(experience.experiencedropoffspot_set.all()) > 0:
        t = experience.experiencedropoffspot_set.filter(language=language)
        if len(t)>0:
            return t[0].dropoff_spot
        else:
            return experience.experiencedropoffspot_set.all()[0].dropoff_spot
    else:
        return None

def get_experience_tags(experience, language):
    tags = []

    if experience.tags is not None and len(experience.tags.all()) > 0:
        t = experience.tags.filter(language=language)
        for i in range(len(t)):
            tags.append(t[i].tag)

    return tags

def get_experience_whatsincluded(experience, language):
    return WhatsIncluded.objects.filter(experience = experience, language = language)

# add new or update experience title
def set_exp_title_all_langs(exp, title, lang, other_lang):
    set_exp_title(exp, title, lang)
    if not has_title_in_other_lang(exp, title, other_lang):
        set_exp_title(exp, title, other_lang)

def has_title_in_other_lang(exp, title, lang):
    title_set = exp.experiencetitle_set.filter(language=lang)
    if len(title_set) > 0:
        title = title_set[0]
        if title.title == '':
            return False
        return True
    else:
        return False

def set_exp_title(exp, title, lang):
    title_set = exp.experiencetitle_set.filter(language=lang)
    if len(title_set) > 0:
        title_set[0].title = title
        title_set[0].save()
    else:
        exp_title = ExperienceTitle(experience=exp, title=title, language=lang)
        exp_title.save()

def set_exp_desc_all_langs(exp, desc, lang, other_lang):
    set_exp_description(exp, desc, lang)
    if not has_desc_in_other_lang(exp, desc, other_lang):
        set_exp_description(exp, desc, other_lang)

def has_desc_in_other_lang(exp, activity, lang):
    desc_set = exp.experiencedescription_set.filter(language=lang)
    if len(desc_set) > 0:
        desc = desc_set[0]
        if desc.description == '':
            return False
        return True
    else:
        return False

def set_exp_description(exp, desc, lang):
    description_set = exp.experiencedescription_set.filter(language=lang)
    if len(description_set) > 0:
        description_set[0].description = desc
        description_set[0].save()
    else:
        exp_desc = ExperienceDescription(experience=exp, description=desc, language=lang)
        exp_desc.save()

def set_exp_activity_all_langs(exp, activity, lang, other_lang):
    set_exp_activity(exp, activity, lang)
    if not has_activity_in_other_lang(exp, activity, other_lang):
        set_exp_activity(exp, activity, other_lang)

def has_activity_in_other_lang(exp, activity, lang):
    activity_set = exp.experienceactivity_set.filter(language=lang)
    if len(activity_set) > 0:
        activity = activity_set[0]
        if activity.activity == '':
            return False
        return True
    else:
        return False

def set_exp_activity(exp, activity, lang):
    activity_set = exp.experienceactivity_set.filter(language=lang)
    if len(activity_set) > 0:
        activity_set[0].activity = activity
        activity_set[0].save()
    else:
        exp_activity = ExperienceActivity(experience=exp, activity=activity, language=lang)
        exp_activity.save()

def set_exp_interaction_all_langs(exp, activity, lang, other_lang):
    set_exp_interaction(exp, activity, lang)
    if not has_interaction_in_other_lang(exp, activity, other_lang):
        set_exp_interaction(exp, activity, other_lang)

def has_interaction_in_other_lang(exp, activity, lang):
    interaction_set = exp.experienceinteraction_set.filter(language=lang)
    if len(interaction_set) > 0:
        interaction = interaction_set[0]
        if interaction.interaction == '':
            return False
        return True
    else:
        return False

def set_exp_interaction(exp, interaction, lang):
    interaction_set = exp.experienceinteraction_set.filter(language=lang)
    if len(interaction_set) > 0:
        interaction_set[0].interaction = interaction
        interaction_set[0].save()
    else:
        exp_interaction = ExperienceInteraction(experience=exp, interaction=interaction, language=lang)
        exp_interaction.save()

def set_exp_dress_all_langs(exp, activity, lang, other_lang):
    set_exp_dress(exp, activity, lang)
    if not has_dress_in_other_lang(exp, activity, other_lang):
        set_exp_dress(exp, activity, other_lang)

def has_dress_in_other_lang(exp, activity, lang):
    dress_set = exp.experiencedress_set.filter(language=lang)
    if len(dress_set) > 0:
        dress = dress_set[0]
        if dress.dress is None or dress.dress == '':
            return False
        else:
            return True
    else:
        return False

def set_exp_dress(exp, dress, lang):
    dress_set = exp.experiencedress_set.filter(language=lang)
    if len(dress_set) > 0:
        dress_set[0].dress = dress
        dress_set[0].save()
    else:
        exp_dress = ExperienceDress(experience=exp, dress=dress, language=lang)
        exp_dress.save()

def set_experience_includes(experience, item, is_include, lang):
    include_set = experience.whatsincluded_set.filter(item=item, language=lang)
    if len(include_set) > 0:
        exp_include = include_set[0]
        exp_include.included = is_include
        exp_include.save()
    else:
        exp_include = WhatsIncluded(item=item, included=is_include, language=lang, experience=experience)
        exp_include.save()

def set_exp_includes_detail_all_langs(exp, item, detail, lang, other_lang):
    set_exp_includes_detail(exp, item, detail, lang)
    if not has_includes_detail_in_other_lang(exp, item, detail, other_lang):
        set_exp_includes_detail(exp, item, detail, other_lang)

def has_includes_detail_in_other_lang(exp, item, detail, lang):
    include_set = exp.whatsincluded_set.filter(item=item, language=lang)
    if len(include_set) > 0:
        exp_include = include_set[0]
        if exp_include.details == '':
            return False
        return True
    else:
        return False

def set_exp_includes_detail(exp, item, detail, lang):
    include_set = exp.whatsincluded_set.filter(item=item, language=lang)
    if len(include_set) > 0:
        exp_include = include_set[0]
        exp_include.details = detail
        exp_include.save()
    else:
        exp_include = WhatsIncluded(item=item, details=detail, language=lang, experience=exp)
        exp_include.save()

def set_exp_meetup_spot(exp, meetup_spot, lang):
    meetup_spot_set = exp.experiencemeetupspot_set.filter(language=lang)
    if len(meetup_spot_set) > 0:
        exp_meetup_spot = meetup_spot_set[0]
        exp_meetup_spot.meetup_spot = meetup_spot
        exp_meetup_spot.save()
    else:
        exp_meetup_spot = ExperienceMeetupSpot(meetup_spot=meetup_spot, language=lang, experience=exp)
        exp_meetup_spot.save()

def set_exp_dropoff_spot(exp, dropoff_spot, lang):
    dropoff_spot_set = exp.experiencedropoffspot_set.filter(language=lang)
    if len(dropoff_spot_set) > 0:
        exp_dropoff_spot = dropoff_spot_set[0]
        exp_dropoff_spot.dropoff_spot = dropoff_spot
        exp_dropoff_spot.save()
    else:
        exp_dropoff_spot = ExperienceDropoffSpot(dropoff_spot=dropoff_spot, language=lang, experience=exp)
        exp_dropoff_spot.save()

def has_meetup_spot_in_other_lang(exp, lang):
    meetup_spot_set = exp.experiencemeetupspot_set.filter(language=lang)
    if len(meetup_spot_set) > 0:
        exp_meetup_spot = meetup_spot_set[0]
        if exp_meetup_spot.meetup_spot == '':
            return False
        return True
    else:
        return False

def has_dropoff_spot_in_other_lang(exp, lang):
    dropoff_spot_set = exp.experiencedropoffspot_set.filter(language=lang)
    if len(dropoff_spot_set) > 0:
        exp_dropoff_spot = dropoff_spot_set[0]
        if exp_dropoff_spot.dropoff_spot == '':
            return False
        return True
    else:
        return False

def set_exp_meetup_spot_all_langs(exp, meetup_spot, lang, other_lang):
    set_exp_meetup_spot(exp, meetup_spot, lang)
    if not has_meetup_spot_in_other_lang(exp, other_lang):
        set_exp_meetup_spot(exp, meetup_spot, other_lang)

def set_exp_dropoff_spot_all_langs(exp, meetup_spot, lang, other_lang):
    set_exp_dropoff_spot(exp, meetup_spot, lang)
    if not has_dropoff_spot_in_other_lang(exp, other_lang):
        set_exp_dropoff_spot(exp, meetup_spot, other_lang)

