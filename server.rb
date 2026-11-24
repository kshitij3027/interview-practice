require_relative 'lib/http'
store = Store.new(File.join(__dir__, 'fixtures/sites.json'))
app = Http.new(store, File.join(__dir__, 'public'))
server = WEBrick::HTTPServer.new(Port: Integer(ENV.fetch('PORT','8080')), BindAddress: '127.0.0.1')
server.mount_proc('/') { |req,res| app.call(req,res) }
trap('INT') { server.shutdown }
server.start
