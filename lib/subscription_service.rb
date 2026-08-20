# frozen_string_literal: true

require 'date'

class SubscriptionService
  class ValidationError < StandardError; end
  class ConflictError < StandardError; end

  def initialize(store)
    @store = store
  end

  def list_accounts
    @store.accounts.map do |account|
      {
        'id' => account['id'],
        'name' => account['name'],
        'revision' => account['revision'],
        'current_plan_key' => plan_on(account['segments'], @store.business_date)
      }
    end
  end

  def account_detail(id)
    account = @store.account(id)
    return nil unless account
    account.merge('current_plan_key' => plan_on(account['segments'], @store.business_date))
  end

  def plans
    @store.plans
  end

  def change_current_plan(id:, plan_key:, expected_revision:)
    validate_active_plan!(plan_key)
    business_date = Date.iso8601(@store.business_date)

    updated = @store.mutate_account(id) do |account|
      raise ConflictError, 'account revision changed' unless account['revision'] == expected_revision

      current = account['segments'].find do |segment|
        start_on = Date.iso8601(segment['start_on'])
        end_on = segment['end_on'] && Date.iso8601(segment['end_on'])
        start_on <= business_date && (end_on.nil? || business_date < end_on)
      end
      raise ValidationError, 'no plan is effective on the business date' unless current

      current['plan_key'] = plan_key
      account['segments'] = coalesce(account['segments'])
      account['revision'] += 1
    end

    updated && updated.merge('current_plan_key' => plan_on(updated['segments'], @store.business_date))
  end

  private

  def validate_active_plan!(plan_key)
    plan = @store.plans.find { |candidate| candidate['key'] == plan_key }
    raise ValidationError, 'unknown plan' unless plan
    raise ValidationError, 'plan is inactive' unless plan['active']
  end

  def plan_on(segments, date_string)
    date = Date.iso8601(date_string)
    segment = segments.find do |candidate|
      start_on = Date.iso8601(candidate['start_on'])
      end_on = candidate['end_on'] && Date.iso8601(candidate['end_on'])
      start_on <= date && (end_on.nil? || date < end_on)
    end
    segment && segment['plan_key']
  end

  def coalesce(segments)
    ordered = segments.sort_by { |segment| segment['start_on'] }
    result = []
    ordered.each do |segment|
      if result.any? && result.last['plan_key'] == segment['plan_key'] && result.last['end_on'] == segment['start_on']
        result.last['end_on'] = segment['end_on']
      else
        result << segment.dup
      end
    end
    result
  end
end
