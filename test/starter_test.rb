require 'minitest/autorun'
require_relative '../lib/http'
class StarterTest < Minitest::Test
  Request = Struct.new(:request_method,:path,:query_string,:body)
  class Response
    attr_accessor :status,:body
    def initialize; @status=200; @headers={}; end
    def []=(k,v); @headers[k]=v; end
  end
  def setup
    @store=Store.new(File.expand_path('../fixtures/sites.json',__dir__))
    @http=Http.new(@store,File.expand_path('../public',__dir__))
  end
  def request(method,path,query={},body=nil)
    res=Response.new
    @http.call(Request.new(method,path,URI.encode_www_form(query),body && JSON.generate(body)),res)
    [res.status,JSON.parse(res.body)]
  end
  def test_search
    assert_equal ['m1'],@store.meters('harbor',' LINE ')['meters'].map{|m|m['id']}
  end
  def test_detail
    assert_equal %w[r1 r2 r4 r5 r3 r6 r7],@store.detail('harbor','m1')['readings'].map{|r|r['id']}
  end
  def test_scope
    assert_equal 404,request('GET','/api/meters/m4',{'site'=>'harbor'})[0]
  end
  def test_review_and_stale
    path='/api/meters/m1/readings/r1/review'; q={'site'=>'harbor'}
    status,d=request('POST',path,q,{'expectedRevision'=>3,'review'=>'rejected'})
    assert_equal 200,status; assert_equal 4,d['revision']
    assert_equal 409,request('POST',path,q,{'expectedRevision'=>3,'review'=>'accepted'})[0]
    assert_equal 'rejected',@store.detail('harbor','m1')['readings'].first['review']
    assert_equal 1,@store.meters('ridge')['revision']
  end
  def test_noop
    assert_equal 3,@store.review('harbor','m1','r1',{'expectedRevision'=>3,'review'=>'accepted'})['revision']
  end
  def test_bad_review
    assert_equal 400,request('POST','/api/meters/m1/readings/r1/review',{'site'=>'harbor'},{'expectedRevision'=>true,'review'=>'accepted'})[0]
  end
  def test_list_api
    status,d=request('GET','/api/meters',{'site'=>'harbor'})
    assert_equal 200,status; assert_equal 3,d['meters'].size
  end
end
