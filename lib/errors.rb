class DomainError < StandardError
  attr_reader :status, :details

  def initialize(message, status: 422, details: nil)
    super(message)
    @status = status
    @details = details
  end
end
