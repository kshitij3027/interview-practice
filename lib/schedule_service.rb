require 'time'
require_relative 'errors'

class ScheduleService
  def initialize(store)
    @store = store
  end

  def list_employees
    @store.employees.sort_by { |employee| [employee['name'].downcase, employee['id']] }
  end

  def list_shifts(site: nil)
    shifts = @store.shifts
    shifts = shifts.select { |shift| shift['site'] == site } if site && !site.empty? && site != 'all'
    shifts.sort_by { |shift| [Time.iso8601(shift['starts_at']), shift['site'], shift['id']] }
  end

  def shift_detail(id)
    shift = @store.shift(id)
    raise DomainError.new('shift not found', status: 404) unless shift
    shift
  end

  def reassign(shift_id:, employee_id:, expected_revision:)
    @store.mutex.synchronize do
      snapshot = @store.snapshot
      shift = snapshot['shifts'].find { |item| item['id'] == shift_id }
      raise DomainError.new('shift not found', status: 404) unless shift

      employee = snapshot['employees'].find { |item| item['id'] == employee_id }
      raise DomainError.new('employee not found', status: 404) unless employee

      unless expected_revision.is_a?(Integer) && expected_revision == shift['revision']
        raise DomainError.new(
          'shift revision is stale',
          status: 409,
          details: { 'current_shift' => shift, 'schedule_revision' => snapshot['schedule_revision'] }
        )
      end

      validate_qualification!(employee, shift)
      validate_no_overlap!(snapshot['shifts'], employee_id, shift)

      if shift['employee_id'] == employee_id
        return { 'shift' => shift, 'schedule_revision' => snapshot['schedule_revision'], 'changed' => false }
      end

      updated = @store.update_shift_assignment!(shift_id, employee_id)
      { 'shift' => updated, 'schedule_revision' => @store.schedule_revision, 'changed' => true }
    end
  end

  private

  def validate_qualification!(employee, shift)
    unless employee['sites'].include?(shift['site']) && employee['roles'].include?(shift['role'])
      raise DomainError.new('employee is not qualified for this shift')
    end
  end

  def validate_no_overlap!(shifts, employee_id, candidate_shift)
    candidate_start = Time.iso8601(candidate_shift['starts_at'])
    candidate_end = Time.iso8601(candidate_shift['ends_at'])

    conflict = shifts.find do |other|
      next false if other['id'] == candidate_shift['id'] || other['employee_id'] != employee_id

      other_start = Time.iso8601(other['starts_at'])
      other_end = Time.iso8601(other['ends_at'])
      candidate_start < other_end && other_start < candidate_end
    end

    raise DomainError.new("employee has overlapping shift #{conflict['id']}") if conflict
  end
end
