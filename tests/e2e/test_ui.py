"""Real browser and SQLite. Only admin remote NEU HTTP is mocked for deterministic UI tests."""
from pathlib import Path
import re
import threading
import uuid
import httpx
import pytest
from playwright.sync_api import sync_playwright, expect
from werkzeug.serving import make_server
from werkzeug.security import generate_password_hash
from app import create_app
from app.extensions import db
from app.models import User
from app.services.sync_service import sync_courses

pytestmark=pytest.mark.e2e
SCREENSHOTS=Path(__file__).resolve().parents[2]/'docs/screenshots'

@pytest.fixture(scope='module')
def live_server(tmp_path_factory):
    tmp=tmp_path_factory.mktemp('e2e')
    app=create_app({'TESTING':True,'SQLALCHEMY_DATABASE_URI':'sqlite:///'+str(tmp/'test.db'),'SECRET_KEY':'isolated-e2e-test-only'})
    with app.app_context():
        db.session.add(User(email='admin@e2e.test',name='Quản trị kiểm thử',role='admin',password_hash=generate_password_hash('E2ETestOnly123!'),profile={}))
        db.session.commit()
        from app.services.customer_demo import prepare_customer_demo
        prepare_customer_demo()
    import importlib
    routes=importlib.import_module('app.routes.api')
    original=routes.sync_courses
    payload=[{'type':'subject','subjectCode':'E2E001','name':'Môn từ API kiểm thử','curriculums':[{'year':'K66 - 2024'}]}]
    routes.sync_courses=lambda q:sync_courses(q,httpx.MockTransport(lambda req:httpx.Response(200,json=payload)))
    server=make_server('127.0.0.1',0,app,threaded=True)
    thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
    yield f'http://127.0.0.1:{server.server_port}'
    server.shutdown();routes.sync_courses=original
    with app.app_context():
        db.session.remove()
        db.engine.dispose()

@pytest.fixture(scope='module')
def browser():
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        yield browser
        browser.close()

@pytest.fixture
def page(browser):
    context=browser.new_context(viewport={'width':1440,'height':1000},accept_downloads=True)
    page=context.new_page()
    errors=[]
    page.on('pageerror',lambda error:errors.append(str(error)))
    yield page
    assert not errors,errors
    context.close()

def ready(page,url):
    page.goto(url,wait_until='networkidle')
    expect(page.locator('.loading-state')).to_have_count(0)

def test_logo_upgrades_cached_legacy_template(page,live_server):
    legacy='<a class="brand" href="/"><span class="brand-mark"><i data-lucide="route"></i></span><span>NEU <b>Learning Path</b></span></a>'
    def cached_html(route):
        response=route.fetch()
        html=re.sub(r'<a class="brand"[^>]*>.*?</a>',lambda match:legacy,response.text(),count=1,flags=re.S)
        html=re.sub(r'<a class="mobile-brand"[^>]*>.*?</a>','',html,count=1,flags=re.S)
        route.fulfill(response=response,body=html)
    page.route(live_server+'/',cached_html)
    ready(page,live_server)
    logo=page.locator('.brand img.brand-mark')
    expect(logo).to_be_visible()
    assert logo.evaluate('(img)=>img.complete && img.naturalWidth>0')
    expect(page.locator('.brand-copy strong')).to_have_text('NEU')
    assert page.locator('.brand span.brand-mark').count()==0
    page.set_viewport_size({'width':390,'height':844})
    page.reload(wait_until='networkidle')
    expect(page.locator('.mobile-brand img')).to_be_visible()
    assert page.locator('.mobile-brand img').evaluate('(img)=>img.complete && img.naturalWidth>0')

@pytest.mark.parametrize('width,height',[(1440,1000),(768,1024),(390,844)])
def test_responsive_no_horizontal_overflow(page,live_server,width,height):
    page.set_viewport_size({'width':width,'height':height})
    ready(page,live_server)
    expect(page.locator('.course-card')).to_have_count(10)
    assert page.evaluate('document.documentElement.scrollWidth <= window.innerWidth')
    if width==390:
        page.get_by_role('button',name='Mở điều hướng').click()
        expect(page.locator('#sidebar')).to_have_class('sidebar open')
        page.locator('#mobile-overlay').click(position={'x':350,'y':300})
    SCREENSHOTS.mkdir(parents=True,exist_ok=True)
    page.screenshot(path=str(SCREENSHOTS/f'viewport-{width}.png'),full_page=True)

def test_career_creation_details_graph_compare_and_pdf(page,live_server,tmp_path):
    ready(page,live_server)
    page.get_by_role('button',name='Tạo lộ trình mới',exact=True).click()
    page.locator('#major-input').select_option('7480101')
    page.locator('#cohort-input').select_option('K67 - 2025')
    page.locator('#career-input').select_option('ai')
    page.get_by_role('button',name='Tạo lộ trình của tôi',exact=True).click()
    expect(page.get_by_role('heading',name='Trở thành AI / Machine Learning Engineer')).to_be_visible()
    expect(page.locator('.course-card')).to_have_count(10)
    page.get_by_role('button',name='Môn được gợi ý 10',exact=True).click()
    expect(page.locator('.recommend-item')).to_have_count(15)
    page.locator('.recommend-item [data-action="detail"]').first.click()
    expect(page.get_by_role('heading',name='Kết nối trong đồ thị tri thức')).to_be_visible()
    page.get_by_role('button',name='Xem trên đồ thị').click()
    expect(page.locator('#graph-canvas canvas').first).to_be_visible()
    page.get_by_role('button',name='Đặt lại',exact=True).click()
    # Click a rendered node and edge using Cytoscape's actual rendered coordinates.
    position=page.evaluate("({x:state.graph.nodes().first().renderedPosition('x'),y:state.graph.nodes().first().renderedPosition('y')})")
    page.locator('#graph-canvas').click(position=position)
    expect(page.locator('#graph-info')).not_to_contain_text('Chọn một nút')
    page.locator('#graph-canvas').scroll_into_view_if_needed()
    page.evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))')
    position=page.evaluate('''() => {
        const graph=state.graph;
        const bounds=graph.nodes().map(n=>n.renderedBoundingBox({includeLabels:true}));
        const edge=graph.edges('.highlight').filter(e=>{
            const p=e.renderedMidpoint();
            return p.x>20 && p.y>20 && p.x<graph.width()-20 && p.y<graph.height()-20 &&
                bounds.every(b=>p.x<b.x1-8 || p.x>b.x2+8 || p.y<b.y1-8 || p.y>b.y2+8);
        }).first();
        if(!edge.length)throw new Error('No unoccluded edge midpoint in graph viewport');
        return edge.renderedMidpoint();
    }''')
    page.locator('#graph-canvas').click(position=position)
    expect(page.locator('#graph-info')).to_contain_text('Nguồn:')
    page.get_by_role('button',name='Lộ trình học tập',exact=True).click()
    page.get_by_role('button',name='So sánh định hướng').click()
    page.locator('#compare-career').select_option('security')
    page.get_by_role('button',name='So sánh lộ trình',exact=True).click()
    expect(page.locator('.compare-grid')).to_be_visible()
    page.get_by_role('button',name='Đóng',exact=True).last.click()
    page.get_by_role('button',name='Hướng dẫn',exact=True).click()
    with page.expect_download() as info:
        page.get_by_role('button',name='Xuất PDF lộ trình').click()
    download=info.value
    download.save_as(tmp_path/'roadmap.pdf')
    assert (tmp_path/'roadmap.pdf').read_bytes().startswith(b'%PDF')

def test_graph_search_inspector_zoom_and_reset(page,live_server):
    ready(page,live_server+'/graph')
    expect(page.locator('.graph-hero')).to_be_visible()
    expect(page.locator('[data-graph-count="Course"]')).to_have_text('15')
    page.locator('#graph-search').fill('Python')
    expect(page.locator('#graph-info .graph-neighbor')).to_have_count(2)
    page.locator('#graph-info [data-id="course:DEMO-PY"]').click()
    expect(page.locator('#graph-info .graph-selection-title')).to_have_text('Lập trình Python')
    page.locator('#graph-info [data-action="detail"]').click()
    expect(page.locator('#modal')).to_be_visible()
    expect(page.locator('#modal').get_by_role('heading',name='Lập trình Python',exact=True)).to_be_visible()
    page.get_by_role('button',name='Đóng chi tiết',exact=True).click()
    page.locator('#graph-search').fill('zzzz-no-graph-results')
    expect(page.locator('#graph-info .graph-selection-title')).to_have_text('0 kết quả')
    page.locator('[data-action="graph-reset"]').click()
    expect(page.locator('#graph-search')).to_have_value('')
    expect(page.locator('#graph-info .graph-inspector-welcome')).to_be_visible()
    assert page.evaluate('state.graph.elements(".dim, .highlight").length')==0
    zoom=page.evaluate('state.graph.zoom()')
    page.get_by_role('button',name='Phóng to đồ thị',exact=True).click()
    assert page.evaluate('state.graph.zoom()')>zoom
    page.get_by_role('button',name='Thu nhỏ đồ thị',exact=True).click()
    assert page.evaluate('state.graph.zoom()')==pytest.approx(zoom)


def test_register_login_save_progress_rename_delete(page,live_server):
    ready(page,live_server)
    page.get_by_role('button',name='Lưu lộ trình của tôi',exact=True).click()
    page.get_by_role('button',name='Đăng ký ngay').click()
    page.locator('#auth-name').fill('Sinh viên kiểm thử')
    email=uuid.uuid4().hex+'@e2e.test'
    page.locator('#auth-email').fill(email)
    page.locator('#auth-password').fill('E2EPassword123!')
    page.get_by_role('button',name='Tạo tài khoản',exact=True).click()
    expect(page.locator('#save-form')).to_be_visible()
    page.locator('#path-name').fill('Lộ trình thử nghiệm')
    page.get_by_role('button',name='Lưu lộ trình',exact=True).click()
    expect(page.locator('#modal')).not_to_be_visible()
    page.get_by_role('button',name='Lập trình Python',exact=True).click()
    page.get_by_role('button',name='Đã hoàn thành',exact=True).click()
    expect(page.locator('.status-controls .btn-primary')).to_contain_text('Đã hoàn thành')
    page.get_by_role('button',name='Đóng chi tiết').click()
    expect(page.locator('.ring-center')).to_contain_text('10%')
    ready(page,live_server+'/saved')
    expect(page.get_by_role('heading',name='Lộ trình thử nghiệm',exact=True)).to_be_visible()
    page.get_by_role('button',name='Đổi tên lộ trình').click()
    page.locator('#rename-form input').fill('Lộ trình đã đổi tên')
    page.get_by_role('button',name='Lưu tên mới').click()
    expect(page.get_by_role('heading',name='Lộ trình đã đổi tên',exact=True)).to_be_visible()
    page.get_by_role('button',name='Xóa lộ trình',exact=True).click()
    page.get_by_role('button',name='Giữ lại').click()
    expect(page.locator('.saved-card')).to_have_count(1)
    page.get_by_role('button',name='Xóa lộ trình',exact=True).click()
    page.get_by_role('button',name='Xác nhận xóa').click()
    expect(page.get_by_role('heading',name='Chưa có lộ trình được lưu')).to_be_visible()
    ready(page,live_server+'/profile')
    page.get_by_role('button',name='Đăng xuất tài khoản').click()
    expect(page.locator('.user-info')).to_contain_text('Bạn học mới')
    assert page.request.get(live_server+'/admin').status==403
    page.get_by_role('button',name='Bạn học mới').click()
    page.locator('#auth-email').fill(email)
    page.locator('#auth-password').fill('E2EPassword123!')
    page.get_by_role('button',name='Đăng nhập',exact=True).click()
    expect(page.locator('.user-info')).to_contain_text('Sinh viên kiểm thử')

def test_demo_login_accounts_and_presenter_flow(page,live_server):
    ready(page,live_server)
    page.get_by_role('button',name='Bạn học mới').click()
    expect(page.locator('.demo-login-panel')).to_contain_text('admin@neu-demo.test')
    expect(page.locator('.demo-login-panel')).to_contain_text('Admin@123456')
    page.get_by_role('button',name='Dùng tài khoản Sinh viên',exact=True).click()
    expect(page.locator('#auth-email')).to_have_value('user@neu-demo.test')
    expect(page.locator('#auth-password')).to_have_value('User@123456')
    page.get_by_role('button',name='Đăng nhập',exact=True).click()
    page.wait_for_url(live_server+'/dashboard')
    expect(page.locator('.user-info')).to_contain_text('Nguyễn Minh Anh')
    expect(page.locator('.ring-center')).to_contain_text('40%')
    expect(page.locator('.course-card')).to_have_count(10)
    assert page.request.get(live_server+'/admin').status==403
    ready(page,live_server+'/saved')
    expect(page.locator('.saved-card')).to_have_count(3)
    ready(page,live_server+'/profile')
    expect(page.locator('#profile-name')).to_have_value('Nguyễn Minh Anh')
    page.get_by_role('button',name='Đăng xuất tài khoản',exact=True).click()
    page.get_by_role('button',name='Bạn học mới').click()
    page.get_by_role('button',name='Dùng tài khoản Quản trị viên',exact=True).click()
    page.get_by_role('button',name='Đăng nhập',exact=True).click()
    page.wait_for_url(live_server+'/admin')
    expect(page.locator('.admin-tabs')).to_be_visible()
    expect(page.locator('.user-info')).to_contain_text('Quản trị viên demo')
    expect(page.locator('.nav-link[href="/admin"]')).to_be_visible()


def test_catalog_search_and_career_filter(page,live_server):
    ready(page,live_server+'/courses')
    expect(page.locator('.course-card')).to_have_count(15)
    page.locator('#course-search').fill('Python')
    expect(page.locator('.course-card')).to_have_count(1)
    page.locator('#course-search').fill('không tồn tại')
    expect(page.get_by_role('heading',name='Chưa tìm thấy môn học')).to_be_visible()
    ready(page,live_server+'/careers')
    page.locator('#career-search').fill('Backend')
    expect(page.locator('.career-card:visible')).to_have_count(1)

def test_admin_sync_and_permissions(page,live_server):
    ready(page,live_server)
    page.get_by_role('button',name='Bạn học mới').click()
    page.locator('#auth-email').fill('admin@e2e.test')
    page.locator('#auth-password').fill('E2ETestOnly123!')
    page.get_by_role('button',name='Đăng nhập',exact=True).click()
    expect(page.locator('.user-info')).to_contain_text('Quản trị kiểm thử')
    ready(page,live_server+'/admin')
    page.get_by_role('button',name='Đồng bộ dữ liệu',exact=True).click()
    page.get_by_role('button',name='Đồng bộ API NEU',exact=True).click()
    expect(page.locator('.data-table')).to_contain_text('Thành công')
    page.screenshot(path=str(SCREENSHOTS/'admin.png'),full_page=True)
    page.get_by_role('button',name='Chương trình',exact=True).click()
    page.get_by_role('button',name='Nhóm học phần',exact=True).first.click()
    expect(page.locator('#membership-items')).to_contain_text('DEMO-')
    page.locator('#membership-source').fill('Bộ dữ liệu E2E: nguồn kiểm thử')
    page.get_by_role('button',name='Lưu nhóm học phần').click()
    expect(page.locator('#modal')).not_to_be_visible()
    ready(page,live_server+'/courses')
    page.locator('#catalog-source').select_option('NEU')
    expect(page.get_by_role('button',name='Môn từ API kiểm thử',exact=True)).to_be_visible()

def test_offline_demo_has_no_remote_asset_requests(page,live_server):
    remote=[]
    def route(request):
        if request.request.url.startswith(live_server):
            request.continue_()
        else:
            remote.append(request.request.url)
            request.abort()
    page.route('**/*',route)
    ready(page,live_server)
    expect(page.locator('.course-card')).to_have_count(10)
    page.get_by_role('button',name='Kỹ năng mục tiêu',exact=True).click()
    expect(page.locator('#skill-chart')).to_be_visible()
    assert remote==[]
