require 'uri'
require_relative 'errors'
require_relative 'http_helpers'

class Router
  def initialize(service, root: File.expand_path('..', __dir__))
    @service = service
    @web_root = File.join(root, 'web')
  end

  def call(request, response)
    path = request.path

    if path.start_with?('/api/')
      route_api(request, response)
    else
      serve_static(path, response)
    end
  rescue DomainError => error
    payload = { 'error' => error.message }
    payload['details'] = error.details if error.details
    HttpHelpers.json(response, error.status, payload)
  rescue StandardError => error
    warn error.full_message
    HttpHelpers.json(response, 500, { 'error' => 'internal server error' })
  end

  private

  def route_api(request, response)
    case [request.request_method, request.path]
    when ['GET', '/api/health']
      HttpHelpers.json(response, 200, { 'ok' => true })
    when ['GET', '/api/employees']
      HttpHelpers.json(response, 200, { 'employees' => @service.list_employees })
    when ['GET', '/api/shifts']
      site = request.query['site']
      shifts = @service.list_shifts(site: site)
      HttpHelpers.json(response, 200, { 'shifts' => shifts })
    else
      if request.request_method == 'GET' && request.path =~ %r{\A/api/shifts/([^/]+)\z}
        HttpHelpers.json(response, 200, { 'shift' => @service.shift_detail(Regexp.last_match(1)) })
      elsif request.request_method == 'PATCH' && request.path =~ %r{\A/api/shifts/([^/]+)/assignee\z}
        body = HttpHelpers.parse_json(request)
        result = @service.reassign(
          shift_id: Regexp.last_match(1),
          employee_id: body['employee_id'],
          expected_revision: body['expected_revision']
        )
        HttpHelpers.json(response, 200, result)
      else
        HttpHelpers.json(response, 404, { 'error' => 'not found' })
      end
    end
  end

  def serve_static(path, response)
    relative = path == '/' ? 'index.html' : path.sub(%r{\A/}, '')
    full_path = File.expand_path(relative, @web_root)
    unless full_path.start_with?(@web_root) && File.file?(full_path)
      response.status = 404
      response.body = 'Not found'
      return
    end

    response.status = 200
    response['Content-Type'] = content_type(full_path)
    response.body = File.binread(full_path)
  end

  def content_type(path)
    case File.extname(path)
    when '.html' then 'text/html; charset=utf-8'
    when '.js' then 'text/javascript; charset=utf-8'
    when '.css' then 'text/css; charset=utf-8'
    else 'application/octet-stream'
    end
  end
end
