export class ApiError extends Error {
  constructor(status, code, message, details = {}) {
    super(message); this.status = status; this.code = code; this.details = details;
  }
}
export const bad = (code, message) => new ApiError(400, code, message);
export const notFound = () => new ApiError(404, 'not_found', 'Case not found');
