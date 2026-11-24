require 'json'
require 'thread'
class ApiError < StandardError
  attr_reader :status, :details
  def initialize(status, message, details = {})
    super(message)
    @status, @details = status, details
  end
end
class Store
  def initialize(path)
    @data = JSON.parse(File.read(path))
    @lock = Mutex.new
  end
  def sites
    @lock.synchronize { copy(@data.fetch('sites')) }
  end
  def meters(site, q = '')
    @lock.synchronize do
      s = site!(site)
      query = q.to_s.strip.downcase
      rows = @data['meters'].select { |m| m['site'] == site && [m['name'], m['id']].any? { |v| v.downcase.include?(query) } }
      copy({'revision'=>s['revision'], 'meters'=>rows.sort_by { |m| m['id'] }})
    end
  end
  def detail(site, id)
    @lock.synchronize do
      s = site!(site)
      m = meter!(site, id)
      copy({'revision'=>s['revision'], 'meter'=>m, 'readings'=>@data['readings'].select { |r| r['meter'] == id }.sort_by { |r| [r['at'], r['seq'], r['id']] }})
    end
  end
  def review(site, meter, id, body)
    @lock.synchronize do
      s = site!(site)
      meter!(site, meter)
      r = @data['readings'].find { |x| x['meter'] == meter && x['id'] == id } or raise ApiError.new(404, 'Unknown reading')
      unless body.is_a?(Hash) && body['expectedRevision'].is_a?(Integer) && body['expectedRevision'] >= 0 && %w[accepted rejected].include?(body['review'])
        raise ApiError.new(400, 'Invalid review')
      end
      raise ApiError.new(409, 'Site changed', {'revision'=>s['revision']}) unless body['expectedRevision'] == s['revision']
      if r['review'] != body['review']
        r['review'] = body['review']
        s['revision'] += 1
      end
      copy({'revision'=>s['revision'], 'reading'=>r})
    end
  end
  private
  def copy(value) = Marshal.load(Marshal.dump(value))
  def site!(id) = @data['sites'].find { |s| s['id'] == id } || raise(ApiError.new(404, 'Unknown site'))
  def meter!(site, id) = @data['meters'].find { |m| m['id'] == id && m['site'] == site } || raise(ApiError.new(404, 'Unknown meter'))
end
