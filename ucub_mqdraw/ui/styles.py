CUSTOM_CSS = """
:root {
    --brand: #123A7A;
    --brand-soft: #EAF1FF;
    --brand-border: #BCD2F3;
    --bg: #EEF3F9;
    --panel: #F8FAFD;
    --card: #FFFFFF;
    --line: #E5EAF2;
    --text: #111827;
    --muted: #6B7280;
}

body {
    background: var(--bg) !important;
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Microsoft YaHei", sans-serif;
    overflow-x: hidden !important;
    width: 100% !important;
}

.gradio-container {
    max-width: none !important;
    width: 100vw !important;
    padding: 0 !important;
    margin: 0 !important;
}

.gradio-container > .main {
    max-width: none !important;
    width: 100% !important;
    padding: 0 !important;
}

.gradio-container .wrap {
    max-width: none !important;
    width: 100% !important;
}

.contain {
    max-width: none !important;
    width: 100% !important;
    padding: 0 !important;
}

#main-shell {
    height: 100vh;
    width: 100vw;
    max-width: 100vw;
    padding: 12px 16px;
    background: var(--bg);
    box-sizing: border-box;
}

#three-column-row {
    display: grid !important;
    grid-template-columns: minmax(480px, 1.25fr) minmax(520px, 1.15fr) minmax(460px, 1.2fr) !important;
    gap: 20px !important;
    height: calc(100vh - 24px) !important;
    width: 100% !important;
    max-width: 100% !important;
    align-items: stretch !important;
    flex-wrap: nowrap !important;
}

#three-column-row > .gap,
#three-column-row > div {
    min-width: 0 !important;
    width: 100% !important;
    max-width: 100% !important;
    flex: unset !important;
}

#left-panel,
#center-panel,
#right-panel {
    background: var(--panel);
    border: 1px solid var(--line);
    border-radius: 18px;
    box-shadow: 0 12px 30px rgba(15, 23, 42, 0.06);
    overflow: hidden;
    width: 100% !important;
    min-width: 0 !important;
    height: 100% !important;
    box-sizing: border-box !important;
}

#left-panel {
    padding: 22px 26px;
    overflow-y: auto !important;
    overflow-x: hidden;
    display: block !important;
}

#left-panel > .column {
    display: flex !important;
    flex-direction: column !important;
    gap: 12px !important;
    height: auto !important;
    min-height: 0 !important;
    flex-shrink: 0 !important;
}

#left-panel #tool-form,
#left-panel .form-card {
    display: flex !important;
    flex-direction: column !important;
    flex-shrink: 0 !important;
    width: 100% !important;
    min-height: 320px !important;
}

#right-panel {
    padding: 20px 24px;
    overflow-y: auto;
    overflow-x: hidden;
}

#center-panel {
    padding: 18px 20px;
    display: flex;
    flex-direction: column;
}

#left-panel .block,
#right-panel .block,
#center-panel .block {
    margin-bottom: 12px !important;
}

#left-panel .form {
    gap: 12px !important;
}

.section-title {
    font-size: 16px;
    font-weight: 800;
    color: var(--text);
    margin-bottom: 10px;
}

.subsection-label {
    font-size: 13px;
    font-weight: 700;
    color: var(--text);
    margin: 6px 0 8px;
}

.top-tabs {
    display: flex;
    gap: 6px;
    overflow-x: auto;
    padding-bottom: 4px;
    margin-bottom: 10px;
    scrollbar-width: none;
}

.top-tabs::-webkit-scrollbar {
    display: none;
}

.top-tab {
    flex: 0 0 auto;
    padding: 7px 12px;
    border-radius: 999px;
    background: #fff;
    border: 1px solid var(--line);
    font-size: 12px;
    color: #374151;
    white-space: nowrap;
}

.top-tab.active {
    background: var(--brand);
    border-color: var(--brand);
    color: #fff;
    box-shadow: 0 4px 10px rgba(18, 58, 122, 0.22);
}

.search-row {
    align-items: center !important;
    gap: 8px !important;
    margin-bottom: 4px !important;
}

#left-panel input,
#right-panel input,
#left-panel textarea {
    border-radius: 12px !important;
    border-color: var(--line) !important;
    box-shadow: none !important;
}

.filter-icon-box {
    height: 38px;
    min-width: 42px;
    border-radius: 12px;
    background: #fff;
    border: 1px solid var(--line);
    display: flex;
    align-items: center;
    justify-content: center;
    color: var(--muted);
    font-size: 12px;
    flex-shrink: 0;
}

.tool-btn-row {
    display: grid !important;
    grid-template-columns: repeat(3, minmax(0, 1fr)) !important;
    gap: 8px !important;
    margin: 0 0 8px 0 !important;
    width: 100% !important;
}

.tool-btn-row-2 {
    grid-template-columns: repeat(2, minmax(0, 1fr)) !important;
}

.tool-btn-row > div {
    min-width: 0 !important;
    width: 100% !important;
}

.upload-row {
    margin-bottom: 6px !important;
    gap: 8px !important;
}

.upload-row button {
    width: 100% !important;
    border-radius: 10px !important;
    border: 1px dashed var(--brand-border) !important;
    background: #F8FBFF !important;
    color: var(--brand) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    min-height: 36px !important;
}

.upload-row button:hover {
    background: #EEF4FF !important;
    border-color: var(--brand) !important;
}

.tool-pick-btn button {
    width: 100% !important;
    min-height: 48px !important;
    height: 48px !important;
    border-radius: 14px !important;
    border: 1px solid var(--line) !important;
    background: #fff !important;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.04) !important;
    font-size: 12px !important;
    font-weight: 600 !important;
    color: #111827 !important;
    padding: 6px 4px !important;
    line-height: 1.3 !important;
}

.tool-pick-active button {
    border-color: var(--brand) !important;
    background: linear-gradient(180deg, #ffffff 0%, #f4f8ff 100%) !important;
    box-shadow: 0 0 0 2px rgba(18, 58, 122, 0.12) !important;
    color: var(--brand) !important;
}

.field-label {
    font-size: 12px;
    font-weight: 600;
    color: var(--text);
    margin: 4px 0 6px;
}

.upload-gap {
    margin-top: 10px !important;
}

.count-pills {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 10px !important;
    margin-bottom: 10px !important;
}

.count-pill button {
    width: 100% !important;
    border-radius: 10px !important;
    border: 1px solid var(--line) !important;
    background: #fff !important;
    font-size: 12px !important;
    padding: 6px 4px !important;
    color: var(--text) !important;
    box-shadow: none !important;
}

.count-pill-active button {
    border-color: var(--brand) !important;
    background: var(--brand-soft) !important;
    color: var(--brand) !important;
    font-weight: 700 !important;
}

.tool-notice {
    font-size: 12px;
    color: var(--muted);
    background: var(--brand-soft);
    border: 1px solid var(--brand-border);
    border-radius: 12px;
    padding: 8px 10px;
    margin-bottom: 10px;
    line-height: 1.5;
}

.form-card {
    background: #fff;
    border-radius: 18px;
    padding: 18px 22px;
    border: 1px solid var(--line);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.05);
    margin-top: 4px;
    width: 100% !important;
    gap: 14px !important;
}

.image-upload-row {
    gap: 18px !important;
    align-items: stretch !important;
    margin-bottom: 6px !important;
}

.image-upload-row > .column,
.image-upload-row > div {
    min-width: 0 !important;
}

.record-header-row {
    align-items: center !important;
    margin-bottom: 8px !important;
}

.form-title-row {
    align-items: center !important;
    margin-bottom: 6px !important;
}

.form-title {
    font-size: 15px;
    font-weight: 800;
    color: var(--text);
}

#base-upload,
#style-upload {
    width: 100% !important;
    flex-shrink: 0 !important;
}

#left-panel #base-upload,
#left-panel #style-upload {
    display: block !important;
    visibility: visible !important;
    opacity: 1 !important;
    margin-bottom: 8px !important;
}

#left-panel #base-upload .upload-container,
#left-panel #style-upload .upload-container,
#left-panel #base-upload .image-container,
#left-panel #style-upload .image-container,
#left-panel #base-upload [data-testid="image-upload"],
#left-panel #style-upload [data-testid="image-upload"] {
    border-radius: 14px !important;
    border: 1px dashed var(--brand-border) !important;
    background: #F8FBFF !important;
    min-height: 140px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
}

#left-panel #base-upload .block-label,
#left-panel #style-upload .block-label {
    font-size: 12px !important;
    font-weight: 600 !important;
    margin-bottom: 6px !important;
    color: #111827 !important;
    display: block !important;
}

#left-panel #base-upload .wrap,
#left-panel #style-upload .wrap {
    padding: 8px !important;
    min-height: 120px !important;
}

#left-panel #base-upload .wrap p,
#left-panel #style-upload .wrap p,
#left-panel #base-upload .wrap span:not(.icon-wrap),
#left-panel #style-upload .wrap span:not(.icon-wrap) {
    font-size: 12px !important;
    color: #6B7280 !important;
}

#left-panel #base-upload .wrap .icon-wrap,
#left-panel #style-upload .wrap .icon-wrap {
    width: 32px !important;
    height: 32px !important;
    color: var(--brand) !important;
    opacity: 0.85;
}

.record-pill button {
    width: 100% !important;
    border-radius: 999px !important;
    font-size: 11px !important;
    padding: 6px 4px !important;
    border: 1px solid var(--line) !important;
    background: #fff !important;
    color: #374151 !important;
    box-shadow: none !important;
}

.record-pill-active button {
    border-color: var(--brand) !important;
    background: var(--brand) !important;
    color: #fff !important;
    font-weight: 600 !important;
}

.strength-row {
    align-items: end !important;
    gap: 8px !important;
}

#preview-wrap {
    position: relative;
    flex: 1;
    min-height: 0;
    height: calc(100vh - 180px);
    background: #fff;
    border-radius: 18px;
    border: 1px dashed #D3DCEB;
    display: flex;
    align-items: center;
    justify-content: center;
    overflow: hidden;
}

#preview-wrap .preview-empty {
    width: 100%;
    height: 100%;
    display: flex !important;
    align-items: center;
    justify-content: center;
    margin: 0 !important;
    padding: 0 !important;
    border: none !important;
    background: transparent !important;
}

#main-preview {
    width: 100%;
    height: 100%;
    flex: 1;
    min-height: 0;
}

#main-preview .image-container,
#main-preview .wrap {
    border: none !important;
    background: transparent !important;
    min-height: 100% !important;
    height: 100% !important;
}

.empty-preview-box {
    text-align: center;
    color: #6B7280;
}

.empty-preview-icon {
    width: 58px;
    height: 58px;
    margin: 0 auto 12px;
    border-radius: 18px;
    background: var(--brand-soft);
    color: var(--brand);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 28px;
}

.empty-preview-title {
    font-size: 15px;
    font-weight: 700;
    color: #111827;
}

.empty-preview-subtitle {
    font-size: 12px;
    margin-top: 6px;
    color: #6B7280;
}

#mask-editor {
    width: 100%;
    height: 100%;
    flex: 1;
    min-height: 0;
}

#mask-editor .image-container,
#mask-editor .wrap {
    border: none !important;
    background: transparent !important;
    min-height: 100% !important;
    height: 100% !important;
}

.center-bottom-buttons {
    display: grid;
    grid-template-columns: 1fr 1fr 1.4fr;
    gap: 10px;
    padding-top: 12px;
    flex-shrink: 0;
}

.mask-action-btn button {
    border-color: var(--brand-border) !important;
    color: var(--brand) !important;
    background: #F8FBFF !important;
}

#submit-btn {
    background: var(--brand) !important;
    color: #fff !important;
    border-radius: 13px !important;
    border: none !important;
    font-weight: 700 !important;
    box-shadow: 0 8px 18px rgba(18, 58, 122, 0.24);
}

#submit-btn:hover {
    background: #0E2E62 !important;
}

.record-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
}

.record-tabs {
    display: grid !important;
    grid-template-columns: repeat(4, minmax(0, 1fr)) !important;
    gap: 6px !important;
    margin-bottom: 12px !important;
}

.record-tabs button {
    width: 100% !important;
    border-radius: 999px !important;
    font-size: 11px !important;
    padding: 6px 4px !important;
    border: 1px solid var(--line) !important;
    background: #fff !important;
    color: #374151 !important;
    box-shadow: none !important;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

.record-tabs .record-pill-active button {
    border-color: var(--brand) !important;
    background: var(--brand) !important;
    color: #fff !important;
}

.record-tabs button:hover {
    border-color: var(--brand-border) !important;
    background: var(--brand-soft) !important;
}

.task-card {
    background: var(--card);
    border-radius: 16px;
    border: 1px solid var(--line);
    padding: 12px;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.05);
    margin-bottom: 12px;
}

.task-card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
}

.task-id,
.task-time {
    color: #9ca3af;
    font-size: 12px;
}

.task-type {
    margin-top: 8px;
    font-size: 14px;
    font-weight: 700;
}

.task-desc {
    color: #4b5563;
    font-size: 13px;
    margin-top: 8px;
    line-height: 1.5;
}

.empty-record {
    background: #fff;
    border: 1px dashed #D3DCEB;
    border-radius: 16px;
    padding: 34px 12px;
    text-align: center;
    color: var(--muted);
    font-size: 13px;
}

.empty-record-icon {
    font-size: 28px;
    margin-bottom: 8px;
}

.empty-record-title {
    font-weight: 700;
    color: #374151;
}

.empty-record-sub {
    font-size: 12px;
    margin-top: 6px;
    color: var(--muted);
}

.status-badge {
    display: inline-block;
    padding: 4px 9px;
    border-radius: 999px;
    font-size: 12px;
    font-weight: 700;
}

.status-success {
    color: #047857;
    background: #D1FAE5;
}

.status-running {
    color: #1D4ED8;
    background: #DBEAFE;
}

.status-failed {
    color: #B91C1C;
    background: #FEE2E2;
}

.progress-bar {
    height: 8px;
    border-radius: 999px;
    background: #DBEAFE;
    overflow: hidden;
    margin-top: 8px;
}

.progress-inner {
    height: 100%;
    background: #2563EB;
    border-radius: 999px;
}

.thumb-row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 10px;
}

.thumb-img,
.thumb-placeholder {
    height: 82px;
    width: 100%;
    border-radius: 12px;
    object-fit: cover;
    background: #F3F4F6;
    border: 1px solid #E5E7EB;
}

.thumb-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #9CA3AF;
    font-size: 12px;
}

.task-actions {
    display: flex;
    gap: 8px;
    margin-top: 10px;
}

.mini-btn {
    flex: 1;
    border: 1px solid #e5e7eb;
    background: #fff;
    border-radius: 8px;
    padding: 6px 8px;
    font-size: 12px;
    color: #374151;
}

.error-message {
    margin-top: 10px;
    color: #dc2626;
    font-size: 13px;
}

#left-panel button,
#center-panel button,
#right-panel button {
    border-radius: 12px !important;
}

.submit-result {
    font-size: 12px;
    color: var(--muted);
    margin-top: 8px;
    min-height: 20px;
}
"""
