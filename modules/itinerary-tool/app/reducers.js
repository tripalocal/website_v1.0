import { combineReducers } from 'redux'
import { reducer as formReducer } from 'redux-form'
import update from 'react-addons-update'

function modal(state = {date: '', field: '', display: 'NONE'}, action) {
  switch (action.type) {
    case 'SHOW_MODAL':
      return update(state, {
        date: {$set: action.date},
        field: {$set: action.field},
        display: {$set: action.setting}
      })
    default:
      return state
  }
}

function dates(state = {}, action) {
  switch (action.type) {
    case 'SHOW_SELECT':
      return update(state, {
        [action.date]: {[action.field]: {display: {$set: action.setting}}}
      })
    case 'UPDATE_ITEMS':
      return update(state, {
        [action.date]: {[action.field]: {items: {$set: action.value}}} 
      })
    case 'ASSIGN_HOST':
      return update(state, {
        [action.date]: {[action.field]: {host: {$set: action.host}}}
      })
    default:
      return state
  }
}

const rootReducer = combineReducers({
  modal,
  dates,
  form: formReducer
})

export default rootReducer