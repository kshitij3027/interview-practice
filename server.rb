# frozen_string_literal: true

require 'webrick'
require_relative 'lib/store'
require_relative 'lib/subscription_service'
require_relative 'lib/routes'

store = Store.new
service = SubscriptionService.new(store)
routes = Routes.new(service)

server = WEBrick::HTTPServer.new(Port: Integer(ENV.fetch('PORT', '3001')), BindAddress: '127.0.0.1', AccessLog: [], Logger: WEBrick::Log.new($stderr, WEBrick::Log::WARN))
server.mount_proc('/') { |req, res| routes.call(req, res) }
trap('INT') { server.shutdown }
trap('TERM') { server.shutdown }
server.start
