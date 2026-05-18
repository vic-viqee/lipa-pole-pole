import api from './api'

export const getPlans = () => api.get('/plans/')
export const getPlan = (id) => api.get(`/plans/${id}`)
export const createPlan = (data) => api.post('/plans/', data)
export const trackPlan = (trackingToken) => api.get(`/plans/track/${trackingToken}`)
export const recordPayment = (data) => api.post('/payments/', data)
export const getPaymentsForPlan = (planId) => api.get(`/payments/plan/${planId}`)
export const getPaymentsPublic = (trackingToken) => api.get(`/payments/public/${trackingToken}`)
export const initiateMpesaPayment = (trackingToken, phone, amount) =>
  api.post(`/payments/mpesa/stk/${trackingToken}?phone=${phone}&amount=${amount}`)
