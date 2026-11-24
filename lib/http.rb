require 'webrick'
require 'uri'
require_relative 'store'
class Http
  def initialize(store, public_dir)
    @store, @public_dir = store, public_dir
  end
  def call(req, res)
    if req.path.start_with?('/api/')
      res['Content-Type'] = 'application/json; charset=utf-8'
      res['Cache-Control'] = 'no-store'
      res.body = JSON.generate(dispatch(req))
    else
      name = {'/'=>'index.html','/app.js'=>'app.js','/api.js'=>'api.js','/styles.css'=>'styles.css'}[req.path]
      raise ApiError.new(404, 'Not found') unless name && req.request_method == 'GET'
      res['Content-Type'] = {'html'=>'text/html','js'=>'text/javascript','css'=>'text/css'}[name.split('.').last]
      res.body = File.read(File.join(@public_dir, name))
    end
  rescue ApiError => e
    res.status = e.status
    res['Content-Type'] = 'application/json'
    res.body = JSON.generate({'error'=>e.message}.merge(e.details))
  rescue JSON::ParserError
    res.status = 400
    res['Content-Type'] = 'application/json'
    res.body = JSON.generate({'error'=>'Invalid JSON'})
  end
  def dispatch(req)
    q = URI.decode_www_form(req.query_string.to_s).to_h
    method = req.request_method
    path = req.path
    return @store.sites if method == 'GET' && path == '/api/sites'
    return @store.meters(q['site'], q['q']) if method == 'GET' && path == '/api/meters'
    if method == 'GET' && (m = %r{\A/api/meters/([^/]+)\z}.match(path))
      return @store.detail(q['site'], m[1])
    end
    if method == 'POST' && (m = %r{\A/api/meters/([^/]+)/readings/([^/]+)/review\z}.match(path))
      return @store.review(q['site'], m[1], m[2], JSON.parse(req.body.to_s))
    end
    raise ApiError.new(404, 'Not found')
  end
end
