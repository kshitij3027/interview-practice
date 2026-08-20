# frozen_string_literal: true

require 'json'

module HttpHelpers
  def json(res, status, payload)
    res.status = status
    res['Content-Type'] = 'application/json'
    res['Access-Control-Allow-Origin'] = '*'
    res['Access-Control-Allow-Headers'] = 'Content-Type'
    res['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    res.body = JSON.generate(payload)
  end

  def parse_json(req)
    body = req.body.to_s
    body.empty? ? {} : JSON.parse(body)
  rescue JSON::ParserError
    raise ArgumentError, 'invalid JSON body'
  end
end
