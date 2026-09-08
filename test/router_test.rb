require 'minitest/autorun'
require 'json'
require 'stringio'
require_relative '../lib/store'
require_relative '../lib/schedule_service'
require_relative '../lib/router'

FakeRequest = Struct.new(:request_method, :path, :query, :body)
FakeResponse = Struct.new(:status, :body, :headers) do
  def initialize
    super(nil, nil, {})
  end
  def []=(key, value)
    headers[key] = value
  end
end

class RouterTest < Minitest::Test
  def setup
    @router = Router.new(ScheduleService.new(Store.new))
  end

  def call(method, path, query: {}, body: '')
    response = FakeResponse.new
    @router.call(FakeRequest.new(method, path, query, body), response)
    [response.status, JSON.parse(response.body)]
  end

  def test_health_endpoint
    status, body = call('GET', '/api/health')
    assert_equal 200, status
    assert_equal true, body['ok']
  end

  def test_reassignment_endpoint
    status, body = call('PATCH', '/api/shifts/shift-203/assignee', body: JSON.generate({ employee_id: 'emp-105', expected_revision: 1 }))
    assert_equal 200, status
    assert_equal 'emp-105', body['shift']['employee_id']
  end
end
