import React, { PropTypes } from 'react'
import Row from './Row'

const Table = ({ dates }) => (
  <table className="table">
    <thead>
      <tr>
        <th>Date</th>
        <th>City</th>
        <th>Activities</th>
        <th>Transport</th>
        <th>Accommodation</th>
        <th>Restaurants</th>
      </tr>
    </thead>
    <tbody>
      {Object.keys(dates).sort((a,b) => new Date(a) - new Date(b)).map(date => <Row key={date} date={date} fields={dates[date]} />)}
    </tbody>
  </table>
)

Table.propTypes = {
  dates: PropTypes.object
}

export default Table