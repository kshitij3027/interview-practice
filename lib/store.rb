require 'json'
require 'thread'

class Store
  attr_reader :mutex

  def initialize(root: File.expand_path('..', __dir__))
    @root = root
    @mutex = Mutex.new
    reset!
  end

  def reset!
    @mutex.synchronize do
      @employees = JSON.parse(File.read(File.join(@root, 'fixtures', 'employees.json')))
      @shifts = JSON.parse(File.read(File.join(@root, 'fixtures', 'shifts.json')))
      @schedule_revision = 1
    end
  end

  def employees
    deep_copy(@employees)
  end

  def shifts
    deep_copy(@shifts)
  end

  def schedule_revision
    @schedule_revision
  end

  def employee(id)
    item = @employees.find { |employee| employee['id'] == id }
    item && deep_copy(item)
  end

  def shift(id)
    item = @shifts.find { |shift| shift['id'] == id }
    item && deep_copy(item)
  end

  def update_shift_assignment!(shift_id, employee_id)
    shift = @shifts.find { |item| item['id'] == shift_id }
    raise "missing shift #{shift_id}" unless shift

    shift['employee_id'] = employee_id
    shift['revision'] += 1
    @schedule_revision += 1
    deep_copy(shift)
  end

  def snapshot
    {
      'employees' => deep_copy(@employees),
      'shifts' => deep_copy(@shifts),
      'schedule_revision' => @schedule_revision
    }
  end

  private

  def deep_copy(value)
    Marshal.load(Marshal.dump(value))
  end
end
