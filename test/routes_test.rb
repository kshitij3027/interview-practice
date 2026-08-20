# frozen_string_literal: true

require 'minitest/autorun'
require 'json'
require_relative '../lib/store'
require_relative '../lib/subscription_service'
require_relative '../lib/routes'

FakeReq = Struct.new(:request_method, :path, :body)
class FakeRes
  attr_accessor :status, :body
  def initialize = (@headers = {})

  def []=(key, value)
    @headers[key] = value
  end

  def [](key)
    @headers[key]
  end
end

class RoutesTest < Minitest::Test
  def setup
    @routes = Routes.new(SubscriptionService.new(Store.new))
  end

  def request(method, path, body = nil)
    res = FakeRes.new
    @routes.call(FakeReq.new(method, path, body), res)
    [res.status, JSON.parse(res.body)]
  end

  def test_get_account
    status, payload = request('GET', '/api/accounts/acct-202')
    assert_equal 200, status
    assert_equal 'Brightlane Health', payload.dig('account', 'name')
  end

  def test_current_plan_conflict_is_409
    body = JSON.generate('plan_key' => 'starter', 'expected_revision' => 0)
    status, payload = request('POST', '/api/accounts/acct-202/current-plan', body)
    assert_equal 409, status
    assert_match(/revision/, payload['error'])
  end
end
