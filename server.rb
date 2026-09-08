require 'webrick'
require_relative 'lib/store'
require_relative 'lib/schedule_service'
require_relative 'lib/router'

store = Store.new
service = ScheduleService.new(store)
router = Router.new(service)

port = Integer(ENV.fetch('PORT', '8080'))
server = WEBrick::HTTPServer.new(
  Port: port,
  BindAddress: '0.0.0.0',
  AccessLog: [],
  Logger: WEBrick::Log.new($stderr, WEBrick::Log::WARN)
)
server.mount_proc('/') { |request, response| router.call(request, response) }
trap('INT') { server.shutdown }
trap('TERM') { server.shutdown }
puts "ShiftBoard listening on http://localhost:#{port}"
server.start
