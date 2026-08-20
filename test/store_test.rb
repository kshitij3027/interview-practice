# frozen_string_literal: true

require 'minitest/autorun'
require_relative '../lib/store'

class StoreTest < Minitest::Test
  def setup
    @store = Store.new
  end

  def test_loads_fixture_state
    assert_equal '2026-08-20', @store.business_date
    assert_equal 3, @store.accounts.size
    assert_equal 4, @store.plans.size
  end

  def test_returns_copies_not_live_state
    account = @store.account('acct-101')
    account['name'] = 'mutated'
    refute_equal 'mutated', @store.account('acct-101')['name']
  end
end
