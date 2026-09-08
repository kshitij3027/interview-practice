require 'minitest/autorun'
require_relative '../lib/store'

class StoreTest < Minitest::Test
  def setup
    @store = Store.new
  end

  def test_loads_fixture_state_and_revision
    assert_equal 6, @store.employees.length
    assert_equal 10, @store.shifts.length
    assert_equal 1, @store.schedule_revision
  end

  def test_returns_copies
    shift = @store.shift('shift-201')
    shift['employee_id'] = 'changed-locally'
    assert_equal 'emp-101', @store.shift('shift-201')['employee_id']
  end
end
