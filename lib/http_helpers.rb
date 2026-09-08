require 'json'

module HttpHelpers
  module_function

  def json(response, status, payload)
    response.status = status
    response['Content-Type'] = 'application/json'
    response.body = JSON.generate(payload)
  end

  def parse_json(request)
    body = request.body.to_s
    body.empty? ? {} : JSON.parse(body)
  rescue JSON::ParserError
    raise DomainError.new('invalid JSON body', status: 400)
  end
end
