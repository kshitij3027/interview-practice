# frozen_string_literal: true

require 'json'
require 'thread'

class Store
  attr_reader :business_date

  def initialize(root: File.expand_path('..', __dir__))
    @root = root
    @mutex = Mutex.new
    reset!
  end

  def reset!
    @mutex.synchronize do
      @accounts = JSON.parse(File.read(File.join(@root, 'fixtures/accounts.json')))
      @plans = JSON.parse(File.read(File.join(@root, 'fixtures/plan_catalog.json')))
      @business_date = JSON.parse(File.read(File.join(@root, 'fixtures/system.json'))).fetch('business_date')
    end
  end

  def accounts
    @mutex.synchronize { deep_copy(@accounts) }
  end

  def account(id)
    @mutex.synchronize do
      found = @accounts.find { |a| a['id'] == id }
      found && deep_copy(found)
    end
  end

  def plans
    @mutex.synchronize { deep_copy(@plans) }
  end

  def mutate_account(id)
    @mutex.synchronize do
      account = @accounts.find { |a| a['id'] == id }
      return nil unless account
      yield account
      deep_copy(account)
    end
  end

  private

  def deep_copy(value)
    JSON.parse(JSON.generate(value))
  end
end
