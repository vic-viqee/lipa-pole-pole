import api from './api'

export const getCustomers = () => api.get('/customers/')
export const getCustomer = (id) => api.get(`/customers/${id}`)
export const createCustomer = (data) => api.post('/customers/', data)