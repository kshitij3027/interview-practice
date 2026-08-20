# frozen_string_literal: true

require_relative 'http_helpers'
require_relative 'subscription_service'

class Routes
  include HttpHelpers

  def initialize(service)
    @service = service
  end

  def call(req, res)
    return json(res, 204, {}) if req.request_method == 'OPTIONS'

    case [req.request_method, req.path]
    when ['GET', '/api/health']
      json(res, 200, { 'ok' => true })
    when ['GET', '/api/accounts']
      json(res, 200, { 'accounts' => @service.list_accounts })
    when ['GET', '/api/plans']
      json(res, 200, { 'plans' => @service.plans })
    else
      route_dynamic(req, res)
    end
  rescue SubscriptionService::ConflictError => e
    json(res, 409, { 'error' => e.message })
  rescue SubscriptionService::ValidationError, ArgumentError => e
    json(res, 422, { 'error' => e.message })
  rescue StandardError => e
    warn e.full_message
    json(res, 500, { 'error' => 'internal server error' })
  end

  private

  def route_dynamic(req, res)
    if req.request_method == 'GET' && (match = req.path.match(%r{\A/api/accounts/([^/]+)\z}))
      account = @service.account_detail(match[1])
      return json(res, 404, { 'error' => 'account not found' }) unless account
      return json(res, 200, { 'account' => account })
    end

    if req.request_method == 'POST' && (match = req.path.match(%r{\A/api/accounts/([^/]+)/current-plan\z}))
      body = parse_json(req)
      updated = @service.change_current_plan(
        id: match[1],
        plan_key: body.fetch('plan_key'),
        expected_revision: body.fetch('expected_revision')
      )
      return json(res, 404, { 'error' => 'account not found' }) unless updated
      return json(res, 200, { 'account' => updated })
    end

    json(res, 404, { 'error' => 'not found' })
  end
end
