<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Markdown2PDF</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        :root {
            --bg-primary: #1a1f2b;
            --bg-panel: #252b3a;
            --bg-toolbar: #2d3445;
            --border-color: #3a4154;
            --text-primary: #e6e9f0;
            --text-secondary: #a0a8bc;
            --accent-color: #4d9de0;
            --accent-hover: #3a85c9;
            --preview-bg: #ffffff;
            --preview-text: #1a1f2b;
            --modal-bg: #1e2433;
            --modal-border: #353d4e;
        }

        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        html, body {
            height: 100%;
            overflow: hidden;
        }

        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Helvetica Neue', Arial, sans-serif;
            background-color: var(--bg-primary);
            color: var(--text-primary);
            display: flex;
            flex-direction: column;
        }

        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(10, 12, 20, 0.75);
            backdrop-filter: blur(8px);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 1000;
            opacity: 0;
            visibility: hidden;
            transition: opacity 0.3s ease, visibility 0.3s ease;
        }

        .modal-backdrop.active {
            opacity: 1;
            visibility: visible;
        }

        .modal-content {
            background: var(--modal-bg);
            border: 1px solid var(--modal-border);
            border-radius: 12px;
            width: 90%;
            max-width: 560px;
            padding: 1.8rem;
            position: relative;
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.4);
            max-height: 85vh;
            overflow-y: auto;
            color: var(--text-primary);
        }

        .modal-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 1.2rem;
            padding-bottom: 0.8rem;
            border-bottom: 1px solid var(--border-color);
        }

        .modal-title {
            font-size: 1.4rem;
            font-weight: 600;
        }

        .close-modal {
            background: none;
            border: none;
            color: var(--text-secondary);
            font-size: 1.4rem;
            cursor: pointer;
            padding: 0.2rem;
            transition: color 0.2s;
        }

        .close-modal:hover {
            color: var(--accent-color);
        }

        .modal-body h2 {
            margin: 1rem 0 0.8rem;
            font-size: 1.2rem;
            color: var(--accent-color);
        }

        .modal-body p, .modal-body blockquote {
            margin-bottom: 1rem;
            line-height: 1.6;
            font-size: 0.98rem;
        }

        .modal-body blockquote {
            border-left: 3px solid var(--accent-color);
            padding-left: 1rem;
            color: var(--text-secondary);
            font-style: italic;
        }

        .modal-link-btn {
            display: inline-block;
            background: var(--accent-color);
            color: white;
            padding: 0.55rem 1.2rem;
            border-radius: 6px;
            text-decoration: none;
            font-weight: 600;
            margin-top: 0.5rem;
            transition: background 0.2s;
            border: 1px solid var(--accent-color);
        }

        .modal-link-btn:hover {
            background: var(--accent-hover);
            transform: translateY(-1px);
        }

        .header {
            background-color: rgba(34, 40, 55, 0.85);
            backdrop-filter: blur(6px);
            border-bottom: 1px solid var(--border-color);
            padding: 0.6rem 2rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
            z-index: 100;
            flex-shrink: 0;
        }

        .header-title {
            font-size: 1.15rem;
            font-weight: 600;
        }

        .header-buttons {
            display: flex;
            gap: 0.8rem;
        }

        .header-btn {
            background: rgba(45, 52, 69, 0.6);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.45rem 0.9rem;
            border-radius: 5px;
            font-size: 0.88rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.45rem;
            transition: all 0.2s ease;
        }

        .header-btn:hover {
            background: rgba(77, 157, 224, 0.2);
            border-color: var(--accent-color);
        }

        .main-container {
            flex: 1;
            display: flex;
            padding: 1.2rem 2.4rem;
            gap: 1.2rem;
            overflow: hidden;
        }

        .content-area {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 1.2rem;
            width: 100%;
            height: 100%;
        }

        .panel {
            background: var(--bg-panel);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .toolbar {
            background: var(--bg-toolbar);
            border-bottom: 1px solid var(--border-color);
            padding: 0.55rem 0.8rem;
            display: flex;
            gap: 0.5rem;
            flex-wrap: wrap;
            flex-shrink: 0;
        }

        .tool-btn {
            background: rgba(255, 255, 255, 0.05);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.38rem 0.65rem;
            border-radius: 4px;
            cursor: pointer;
            transition: all 0.2s ease;
            font-size: 0.84rem;
            display: flex;
            align-items: center;
            gap: 0.35rem;
            white-space: nowrap;
            min-width: 70px;
        }

        .tool-btn:hover {
            background: rgba(77, 157, 224, 0.15);
            border-color: var(--accent-color);
            color: var(--accent-color);
        }

        .editor {
            flex: 1;
            padding: 0.9rem;
            font-family: 'Consolas', 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            background: var(--bg-primary);
            color: var(--text-primary);
            border: none;
            outline: none;
            caret-color: var(--accent-color);
            overflow: auto;
        }

        .preview-header {
            background: var(--bg-toolbar);
            border-bottom: 1px solid var(--border-color);
            padding: 0.6rem 0.9rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            justify-content: space-between;
            height: 40px;
            flex-shrink: 0;
        }

        .font-size-control label {
            font-size: 0.84rem;
            color: var(--text-secondary);
        }

        .font-size-select, .document-input-group input {
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            color: var(--text-primary);
            padding: 0.22rem 0.45rem;
            border-radius: 4px;
            font-size: 0.84rem;
        }

        .document-input-group {
            display: flex;
            align-items: center;
            background: var(--bg-primary);
            border: 1px solid var(--border-color);
            border-radius: 4px;
            max-width: 170px;
        }

        .document-extension {
            color: var(--text-secondary);
            padding: 0.22rem 0.45rem;
            font-size: 0.86rem;
            border-left: 1px solid var(--border-color);
            min-width: 30px;
            text-align: center;
        }

        .download-btn {
            background: var(--accent-color);
            color: white;
            border: 1px solid var(--accent-color);
            padding: 0.25rem 0.75rem;
            border-radius: 4px;
            font-size: 0.86rem;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            transition: background-color 0.2s ease;
            font-weight: 500;
        }

        .download-btn:hover {
            background: var(--accent-hover);
        }

        .preview {
            flex: 1;
            padding: 1.2rem;
            overflow: auto;
            display: flex;
            align-items: flex-start;
            justify-content: center;
        }

        .preview-content {
            background: var(--preview-bg);
            color: var(--preview-text);
            padding: 2rem 1.5rem;
            line-height: 1.6;
            font-size: 14px;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.12);
            width: 75%;
            min-width: 300px;
            max-width: 800px;
        }

        /* 🔑 ВАЖНО: стили для таблиц */
        .preview-content table {
            width: 100%;
            table-layout: fixed;
            border-collapse: separate !important;
            border-spacing: 0;
            margin: 1rem 0;
            font-size: inherit;
        }

        .preview-content th,
        .preview-content td {
            border: 1px solid #dee2e6 !important;
            padding: 0.5rem;
            text-align: left;
            word-wrap: break-word;
            font-size: inherit;
        }

        .preview-info-container {
            padding: 0 1.2rem 1rem;
            font-size: 0.86rem;
            color: var(--text-secondary);
        }

        .footer {
            position: absolute;
            bottom: 12px;
            left: 28px;
            font-size: 0.88rem;
            z-index: 10;
        }

        .footer-line1 {
            font-weight: 600;
            color: var(--accent-color);
        }

        .footer-line2 {
            font-weight: 500;
            color: var(--text-secondary);
        }

        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }

        ::-webkit-scrollbar-track {
            background: var(--bg-primary);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--border-color);
            border-radius: 3px;
        }

        @media (max-width: 992px) {
            .content-area {
                grid-template-columns: 1fr;
            }
            .main-container {
                padding: 1rem 1.5rem;
            }
            .preview-content {
                width: 95%;
                padding: 1.5rem 1rem;
            }
        }
    </style>
</head>
<body>
    <!-- Modals -->
    <div class="modal-backdrop" id="modalInfo">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">Информация</div>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <h2>Markdown to PDF</h2>
                <p>Наверное, один из самых старых проектов, который пришлось заново пересоздавать, так как старая версия была не идеальной.</p>
                <p>Я уверен, что данный инструмент поможет многим школьникам и студентам, которые выполняют ДЗ через файлы вроде PDF или DOCX.</p>
                <blockquote>
                    Если говорить по простому, то данный сайт переформатирует текст, написанный через Markdown, в документ типа PDF. В скором времени планируется добавить также DOCX, но это случится когда-нибудь позже.
                </blockquote>
                <p>В частности, хочется сказать, что данный сайт не был полностью написан лично мной, а был переделан и улучшен с помощью нейросети Qwen3-Max.</p>
            </div>
        </div>
    </div>

    <div class="modal-backdrop" id="modalThank">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">Поблагодарить</div>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <p>Если вы хотите поддержать проект — поставьте звезду на GitHub! Это многое значит для меня и помогает развивать инструмент дальше.</p>
                <a href="https://github.com/Aurum2347" target="_blank" class="modal-link-btn">
                    <i class="fab fa-github"></i> Поставить ⭐
                </a>
            </div>
        </div>
    </div>

    <div class="modal-backdrop" id="modalTelegram">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">Telegram</div>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <p>Буду очень благодарен, если вы подпишетесь на мой Telegram-канал! Там публикуются полезные новости и обновления.</p>
                <a href="https://t.me/aurums2347" target="_blank" class="modal-link-btn">
                    <i class="fab fa-telegram"></i> Перейти в канал
                </a>
            </div>
        </div>
    </div>

    <div class="modal-backdrop" id="modalGithub">
        <div class="modal-content">
            <div class="modal-header">
                <div class="modal-title">GitHub</div>
                <button class="close-modal">&times;</button>
            </div>
            <div class="modal-body">
                <p>Исходный код проекта доступен на GitHub. Issues, Pull Requests и звёзды приветствуются!</p>
                <a href="https://github.com/Aurum2347" target="_blank" class="modal-link-btn">
                    <i class="fab fa-github"></i> Перейти на GitHub
                </a>
            </div>
        </div>
    </div>

    <div class="header">
        <div class="header-title">Markdown2PDF</div>
        <div class="header-buttons">
            <button class="header-btn" data-modal="modalInfo">
                <i class="fas fa-info-circle"></i> Информация
            </button>
            <button class="header-btn" data-modal="modalThank">
                <i class="fas fa-heart"></i> Поблагодарить
            </button>
            <button class="header-btn" data-modal="modalTelegram">
                <i class="fab fa-telegram"></i> Telegram
            </button>
            <button class="header-btn" data-modal="modalGithub">
                <i class="fab fa-github"></i> GitHub
            </button>
        </div>
    </div>

    <div class="main-container">
        <div class="content-area">
            <div class="panel">
                <div class="toolbar">
                    <button class="tool-btn" title="Жирный" data-format="bold">
                        <i class="fas fa-bold"></i> Жирный
                    </button>
                    <button class="tool-btn" title="Курсив" data-format="italic">
                        <i class="fas fa-italic"></i> Курсив
                    </button>
                    <button class="tool-btn" title="Ссылка" data-format="link">
                        <i class="fas fa-link"></i> Ссылка
                    </button>
                    <button class="tool-btn" title="Изображение" data-format="image">
                        <i class="fas fa-image"></i> Изображение
                    </button>
                    <button class="tool-btn" title="Таблица" data-format="table">
                        <i class="fas fa-table"></i> Таблица
                    </button>
                    <button class="tool-btn" title="Разрыв" data-format="pageBreak">
                        <i class="fas fa-scissors"></i> Разрыв
                    </button>
                </div>
                <textarea class="editor" id="markdownEditor" placeholder="Начните писать ваш Markdown..."># Добро пожаловать!

Это **жирный** и *курсив*.

| Колонка A | Колонка B |
|-----------|-----------|
| Данные 1  | Данные 2  |

[Пример ссылки](https://example.com)

![Изображение](https://placehold.co/400x200)

---

Разрыв страницы.</textarea>
            </div>

            <div class="panel">
                <div class="preview-header">
                    <div class="font-size-control">
                        <label>Размер текста:</label>
                        <select class="font-size-select" id="fontSizeSelect">
                            <option value="12">12px</option>
                            <option value="14" selected>14px</option>
                            <option value="16">16px</option>
                            <option value="18">18px</option>
                            <option value="20">20px</option>
                        </select>
                    </div>
                    <div style="display: flex; gap: 0.75rem; align-items: center;">
                        <div class="document-input-group">
                            <input type="text" id="documentName" value="document">
                            <div class="document-extension">.pdf</div>
                        </div>
                        <button class="download-btn" id="downloadPdf">
                            <i class="fas fa-download"></i> PDF
                        </button>
                    </div>
                </div>
                <div class="preview">
                    <div class="preview-content" id="previewContent"></div>
                </div>
                <div class="preview-info-container">
                    Документ: <strong id="docNameLabel">document.pdf</strong>
                </div>
            </div>
        </div>
    </div>

    <div class="footer">
        <div class="footer-line1">By Aurum2347</div>
        <div class="footer-line2">Делаем для ЛЮДЕЙ, а не по ГОСТ-у.</div>
    </div>

    <!-- 🔑 Подключаем библиотеки с зависимостями -->
    <script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js"></script>

    <script>
        marked.setOptions({ breaks: true, gfm: true });

        const editor = document.getElementById('markdownEditor');
        const preview = document.getElementById('previewContent');
        const downloadBtn = document.getElementById('downloadPdf');
        const documentNameInput = document.getElementById('documentName');
        const docNameLabel = document.getElementById('docNameLabel');
        const fontSizeSelect = document.getElementById('fontSizeSelect');

        function updatePreview() {
            preview.innerHTML = marked.parse(editor.value);
            docNameLabel.textContent = documentNameInput.value + '.pdf';
        }

        document.querySelectorAll('.tool-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const format = btn.getAttribute('data-format');
                const start = editor.selectionStart;
                const end = editor.selectionEnd;
                let newText = '';
                const selected = editor.value.substring(start, end);
                switch(format) {
                    case 'bold': newText = `**${selected}**`; break;
                    case 'italic': newText = `*${selected}*`; break;
                    case 'link': newText = `[${selected || 'текст'}](https://)`;
                    case 'image': newText = `![${selected || 'альт'}](https://)`;
                    case 'table': newText = '\n| Заголовок 1 | Заголовок 2 |\n|-------------|-------------|\n| Ячейка 1    | Ячейка 2    |\n';
                    case 'pageBreak': newText = '\n\n---\n\n';
                }
                editor.value = editor.value.substring(0, start) + newText + editor.value.substring(end);
                editor.focus();
                updatePreview();
            });
        });

        editor.addEventListener('input', updatePreview);
        documentNameInput.addEventListener('input', () => {
            docNameLabel.textContent = documentNameInput.value + '.pdf';
        });
        fontSizeSelect.addEventListener('change', () => {
            preview.style.fontSize = fontSizeSelect.value + 'px';
        });

        downloadBtn.addEventListener('click', () => {
            const opt = {
                margin: 10,
                filename: `${documentNameInput.value || 'document'}.pdf`,
                image: { type: 'jpeg', quality: 0.98 },
                html2canvas: { scale: 2, useCORS: true },
                jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
            };
            html2pdf().from(preview).set(opt).save();
        });

        // Модалки
        document.querySelectorAll('[data-modal]').forEach(btn => {
            btn.addEventListener('click', () => {
                document.getElementById(btn.dataset.modal).classList.add('active');
                document.body.style.overflow = 'hidden';
            });
        });
        document.querySelectorAll('.close-modal, .modal-backdrop').forEach(el => {
            el.addEventListener('click', (e) => {
                if (e.target.classList.contains('modal-backdrop') || e.target.classList.contains('close-modal')) {
                    document.querySelectorAll('.modal-backdrop').forEach(m => m.classList.remove('active'));
                    document.body.style.overflow = '';
                }
            });
        });

        updatePreview();
    </script>
</body>
</html>
