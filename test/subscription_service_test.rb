# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../lib/store'
require_relative '../lib/subscription_service'

class SubscriptionServiceTest < Minitest::Test
  def setup
    @store = Store.new
    @service = SubscriptionService.new(@store)
  end

  def test_lists_current_plan
    row = @service.list_accounts.find { |account| account['id'] == 'acct-101' }
    assert_equal 'starter', row['current_plan_key']
    assert_equal 3, row['revision']
  end

  def test_immediate_change_preserves_future_boundaries
    updated = @service.change_current_plan(id: 'acct-101', plan_key: 'enterprise', expected_revision: 3)
    assert_equal 4, updated['revision']
    assert_equal 'enterprise', updated['current_plan_key']
    assert_equal ['2026-09-01', '2026-10-15'], updated['segments'].drop(1).map { |segment| segment['start_on'] }
  end

  def test_immediate_change_rejects_stale_revision
    error = assert_raises(SubscriptionService::ConflictError) do
      @service.change_current_plan(id: 'acct-101', plan_key: 'growth', expected_revision: 999)
    end
    assert_match(/revision/, error.message)
    assert_equal 3, @service.account_detail('acct-101')['revision']
  end

  def test_inactive_plan_is_rejected
    assert_raises(SubscriptionService::ValidationError) do
      @service.change_current_plan(id: 'acct-101', plan_key: 'legacy-pro', expected_revision: 3)
    end
  end
end
