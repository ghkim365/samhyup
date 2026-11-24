# -*- coding: utf-8 -*-
"""삼협철망 Cloudflare Pages 배포 패키지(dist_deploy) 빌드.

대흥정밀(builder-dhsteel-sales/build_dist_deploy.py) 구조를 따르되,
기존 dist_deploy 안의 파일을 지우지 않고 최신 소스로 덮어쓰기만 한다.
"""
import os, sys, shutil, glob

sys.stdout.reconfigure(encoding='utf-8')

base_dir = os.path.dirname(os.path.abspath(__file__))
dist_dir = os.path.join(base_dir, 'dist_deploy')
os.makedirs(dist_dir, exist_ok=True)


def copy_file(src, dst, label):
    if os.path.exists(src):
        os.makedirs(os.path.dirname(dst), exist_ok=True)
        shutil.copy2(src, dst)
        print(f'[Copied {label}] {os.path.relpath(dst, dist_dir)}')
        return True
    print(f'[Skipped {label}] not found: {os.path.relpath(src, base_dir)}')
    return False


def copy_tree(src, dst, label):
    if not os.path.isdir(src):
        print(f'[Skipped {label}] not found: {os.path.relpath(src, base_dir)}')
        return
    shutil.copytree(src, dst, dirs_exist_ok=True)
    print(f'[Synced {label}] {os.path.relpath(dst, dist_dir)}/')


# 1. Root web assets
for f in ['index.html', 'index_dashboard.html', 'app.js', 'styles.css',
          'manifest.json', 'sw.js', 'google_apps_script_outbound.js']:
    copy_file(os.path.join(base_dir, f), os.path.join(dist_dir, f), 'Root')

# 2. Cloudflare Pages 라우팅: 루트 접속은 고객용 카탈로그로 (관리자는 푸터 은폐 링크 또는 /admin)
redirects = """# Cloudflare Pages Redirects / Rewrites
/    /catalog/index_catalog.html    302
/admin    /index_dashboard.html    200
/brochure    /catalog/index_brochure.html    200
/gallery/*    /catalog/gallery/:splat    200
/images/*     /catalog/images/:splat     200
"""
with open(os.path.join(base_dir, '_redirects'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(redirects)
with open(os.path.join(dist_dir, '_redirects'), 'w', encoding='utf-8', newline='\n') as f:
    f.write(redirects)
print('[Created] _redirects (/ -> /catalog/index_catalog.html 302)')

# 3. Catalog (최상위 파일 + gallery/images/templates)
catalog_src = os.path.join(base_dir, 'catalog')
catalog_dst = os.path.join(dist_dir, 'catalog')
for name in sorted(os.listdir(catalog_src)):
    p = os.path.join(catalog_src, name)
    if os.path.isfile(p) and not name.endswith('.bak'):
        copy_file(p, os.path.join(catalog_dst, name), 'Catalog')
for folder in ['gallery', 'images', 'templates']:
    copy_tree(os.path.join(catalog_src, folder), os.path.join(catalog_dst, folder), f'Catalog {folder}')

# 4. Plan / reports / sales
for pf in os.listdir(os.path.join(base_dir, 'plan')):
    if pf.endswith(('.html', '.md', '.txt')):
        copy_file(os.path.join(base_dir, 'plan', pf), os.path.join(dist_dir, 'plan', pf), 'Plan')
copy_file(os.path.join(base_dir, 'fax', 'fax_report.html'), os.path.join(dist_dir, 'fax', 'fax_report.html'), 'Fax')
copy_file(os.path.join(base_dir, 'mailling', 'mail_report.html'), os.path.join(dist_dir, 'mailling', 'mail_report.html'), 'Mail')
copy_tree(os.path.join(base_dir, 'sales'), os.path.join(dist_dir, 'sales'), 'Sales')

# 5. 작업 요약 HTML 보고서만 (docx/pptx/pdf/스크립트 등 내부 파일은 제외)
for rp in sorted(glob.glob(os.path.join(base_dir, 'workflow', '*_claude_dashboard_work_summary.html'))):
    copy_file(rp, os.path.join(dist_dir, 'workflow', os.path.basename(rp)), 'Workflow Report')

# 6. 크기 집계
total, count = 0, 0
for root, _, files in os.walk(dist_dir):
    for f in files:
        total += os.path.getsize(os.path.join(root, f))
        count += 1
print('\n==========================================')
print('dist_deploy build complete')
print(f'Total Files: {count}')
print(f'Total Size: {total / (1024 * 1024):.2f} MB')
print('==========================================')
