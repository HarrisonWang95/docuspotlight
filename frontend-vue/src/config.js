const BACKEND_PORT = process.env.BACKEND_PORT || '30267';
const PROTOCOL = process.env.PROTOCOL || 'http';
const K8S_HOST = process.env.K8S_HOST || '172.22.141.90';
export const API_BASE_URL = window.location.hostname === 'localhost' ? `http://localhost:${BACKEND_PORT}` : `${PROTOCOL}://${K8S_HOST}:${BACKEND_PORT}`