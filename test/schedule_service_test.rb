require 'minitest/autorun'
require_relative '../lib/store'
require_relative '../lib/schedule_service'

class ScheduleServiceTest < Minitest::Test
  def setup
    @store = Store.new
    @service = ScheduleService.new(@store)
  end

  def test_filters_and_orders_shifts
    shifts = @service.list_shifts(site: 'OAK')
    assert shifts.all? { |shift| shift['site'] == 'OAK' }
    assert_equal shifts.map { |shift| shift['starts_at'] }.sort, shifts.map { |shift| shift['starts_at'] }
  end

  def test_reassigns_qualified_employee_and_increments_revisions_once
    result = @service.reassign(shift_id: 'shift-203', employee_id: 'emp-105', expected_revision: 1)
    assert result['changed']
    assert_equal 'emp-105', result['shift']['employee_id']
    assert_equal 2, result['shift']['revision']
    assert_equal 2, result['schedule_revision']
  end

  def test_rejects_unqualified_employee
    error = assert_raises(DomainError) do
      @service.reassign(shift_id: 'shift-202', employee_id: 'emp-102', expected_revision: 1)
    end
    assert_match(/not qualified/, error.message)
    assert_equal 1, @store.schedule_revision
  end

  def test_rejects_stale_revision_without_mutation
    error = assert_raises(DomainError) do
      @service.reassign(shift_id: 'shift-201', employee_id: 'emp-103', expected_revision: 99)
    end
    assert_equal 409, error.status
    assert_equal 'emp-101', @store.shift('shift-201')['employee_id']
    assert_equal 1, @store.schedule_revision
  end

  def test_rejects_overlapping_assignment
    error = assert_raises(DomainError) do
      @service.reassign(shift_id: 'shift-201', employee_id: 'emp-102', expected_revision: 1)
    end
    assert_match(/overlapping shift/, error.message)
  end
end
