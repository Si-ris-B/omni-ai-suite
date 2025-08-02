import { useState, useEffect, useRef, useMemo, useCallback } from 'react';
import { CKEditor } from '@ckeditor/ckeditor5-react';
import {
    ClassicEditor,
    Alignment,
    Autoformat,
    AutoImage,
    AutoLink,
    Autosave,
    Base64UploadAdapter,
    BlockQuote,
    Bold,
    Bookmark,
    Code,
    Emoji,
    Essentials,
    FindAndReplace,
    FontBackgroundColor,
    FontColor,
    FontFamily,
    FontSize,
    Fullscreen,
    GeneralHtmlSupport,
    Heading,
    Highlight,
    HorizontalLine,
    HtmlComment,
    HtmlEmbed,
    ImageBlock,
    ImageCaption,
    ImageEditing,
    ImageInline,
    ImageInsert,
    ImageInsertViaUrl,
    ImageResize,
    ImageStyle,
    ImageTextAlternative,
    ImageToolbar,
    ImageUpload,
    ImageUtils,
    Indent,
    IndentBlock,
    Italic,
    Link,
    LinkImage,
    List,
    ListProperties,
    Markdown,
    MediaEmbed,
    Mention,
    PageBreak,
    Paragraph,
    PasteFromMarkdownExperimental,
    PasteFromOffice,
    RemoveFormat,
    ShowBlocks,
    SourceEditing,
    SpecialCharacters,
    SpecialCharactersArrows,
    SpecialCharactersCurrency,
    SpecialCharactersEssentials,
    SpecialCharactersLatin,
    SpecialCharactersMathematical,
    SpecialCharactersText,
    Strikethrough,
    Style,
    Subscript,
    Superscript,
    Table,
    TableCaption,
    TableCellProperties,
    TableColumnResize,
    TableProperties,
    TableToolbar,
    TextPartLanguage,
    TextTransformation,
    Title,
    TodoList,
    Underline,
    WordCount
} from 'ckeditor5';
import 'ckeditor5/ckeditor5.css';
import './RichTextEditor.css';

const DEFAULT_LICENSE_KEY = 'GPL';

/**
 * A reusable and isolated Rich Text Editor component based on CKEditor 5.
 *
 * @param {Object} props - The component props.
 * @param {string} [props.initialContent] - The initial HTML content for the editor.
 * @param {string} [props.placeholder] - Placeholder text when the editor is empty.
 * @param {string} [props.licenseKey] - The CKEditor license key.
 * @param {boolean} [props.showWordCount=true] - Whether to display the word count.
 * @param {boolean} [props.showMenuBar=true] - Whether to show the editor menu bar.
 * @param {boolean} [props.showFullscreen=true] - Whether to include the fullscreen button.
 * @param {Array<string>} [props.toolbarItems] - Custom toolbar items. If not provided, a default set is used.
 * @param {string} [props.height] - CSS height for the editor container (e.g., '400px', 'auto').
 * @param {string} [props.width] - CSS width for the editor container (e.g., '795px', '100%', 'auto').
 * @param {boolean} [props.showExportButtons=true] - Whether to display the export buttons.
 * @param {string} [props.fileName='document'] - Default filename prefix for exports.
 * @param {function(string, Object): void} [props.onContentChange] - Callback function triggered when editor data changes. Receives the new HTML data string and editor context.
 * @param {function(Object): Promise<any>} [props.onSaveToDb] - Optional async function to handle saving to a database. Receives an object with content details.
 * @param {function(Error): void} [props.onExportError] - Callback for handling export/save errors.
 * @param {string} [props.className] - Additional CSS class names for the main container.
 * @param {Object} [props.style] - Inline styles for the main container.
 * @param {boolean} [props.readOnly=false] - If true, the editor will be in read-only mode. Toolbar, export buttons, and word count are automatically hidden.
 * @returns {JSX.Element} The RichTextEditor component.
 */
export default function RichTextEditor({
                                           initialContent = '<p>Hello from CKEditor 5 in React!</p>',
                                           placeholder = 'Type or paste your content here!',
                                           licenseKey = DEFAULT_LICENSE_KEY,
                                           showWordCount = true,
                                           showMenuBar = true,
                                           showFullscreen = true,
                                           toolbarItems = null,
                                           height = 'auto',
                                           width = '795px',
                                           showExportButtons = true,
                                           fileName = 'document',
                                           onContentChange,
                                           onSaveToDb,
                                           onExportError = (error) => console.error('Export error:', error),
                                           className = '',
                                           style = {},
                                           readOnly = false
                                       }) {
    const editorContainerRef = useRef(null);
    const editorRef = useRef(null);
    const editorWordCountRef = useRef(null);
    const editorMenuBarRef = useRef(null);
    const [isLayoutReady, setIsLayoutReady] = useState(false);
    const [editorInstance, setEditorInstance] = useState(null);
    const [isExporting, setIsExporting] = useState(false);

    const effectiveShowMenuBar = readOnly ? false : showMenuBar;
    const effectiveShowExportButtons = readOnly ? false : showExportButtons;
    const effectiveShowWordCount = readOnly ? false : showWordCount;

    useEffect(() => {
        if (editorInstance) {
            if (readOnly) {
                editorInstance.enableReadOnlyMode('external-read-only-lock');
            } else {
                editorInstance.disableReadOnlyMode('external-read-only-lock');
            }
        }
    }, [editorInstance, readOnly]);

    const stripHtmlTags = useCallback((html) => {
        const tempDiv = document.createElement('div');
        tempDiv.innerHTML = html;
        return tempDiv.textContent || tempDiv.innerText || '';
    }, []);

    const downloadFile = useCallback((content, filename, mimeType) => {
        const blob = new Blob([content], { type: mimeType });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = filename;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
    }, []);

    const exportToTxt = useCallback(() => {
        if (!editorInstance) return;
        try {
            const editorData = editorInstance.getData();
            const plainText = stripHtmlTags(editorData);
            downloadFile(plainText, `${fileName}.txt`, 'text/plain');
        } catch (error) {
            onExportError(error);
        }
    }, [editorInstance, fileName, stripHtmlTags, downloadFile, onExportError]);

    const exportToSrt = useCallback(() => {
        if (!editorInstance) return;
        try {
            const editorData = editorInstance.getData();
            const plainText = stripHtmlTags(editorData);
            const lines = plainText.split('\n').filter(line => line.trim());
            let srtContent = '';
            lines.forEach((line, index) => {
                if (line.trim()) {
                    const startTime = formatSrtTime(index * 3);
                    const endTime = formatSrtTime((index + 1) * 3);
                    srtContent += `${index + 1}\n${startTime} --> ${endTime}\n${line.trim()}\n\n`;
                }
            });
            downloadFile(srtContent, `${fileName}.srt`, 'text/srt');
        } catch (error) {
            onExportError(error);
        }
    }, [editorInstance, fileName, stripHtmlTags, downloadFile, onExportError]);

    const formatSrtTime = useCallback((seconds) => {
        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);
        const milliseconds = Math.floor((seconds % 1) * 1000);
        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')},${milliseconds.toString().padStart(3, '0')}`;
    }, []);

    const saveToDatabase = useCallback(async () => {
        if (!editorInstance) return;
        if (!onSaveToDb) {
            const error = new Error('No database save function provided (onSaveToDb prop is missing)');
            onExportError(error);
            return;
        }
        try {
            setIsExporting(true);
            const editorData = editorInstance.getData();
            const result = await onSaveToDb({
                content: editorData,
                plainText: stripHtmlTags(editorData),
                timestamp: new Date(),
                fileName: fileName
            });
            return result;
        } catch (error) {
            onExportError(error);
            return false;
        } finally {
            setIsExporting(false);
        }
    }, [editorInstance, fileName, onSaveToDb, stripHtmlTags, onExportError]);

    const handleEditorChange = useCallback((event, editor) => {
        const data = editor.getData();
        if (onContentChange) {
            onContentChange(data, { event, editor });
        }
    }, [onContentChange]);

    useEffect(() => {
        if (editorInstance && initialContent !== undefined) {
            const currentData = editorInstance.getData();
            if (currentData !== initialContent) {
                editorInstance.setData(initialContent);
            }
        }
    }, [initialContent, editorInstance]);

    useEffect(() => {
        setIsLayoutReady(true);
        return () => setIsLayoutReady(false);
    }, []);

    const defaultToolbarItems = useMemo(() => [
        'undo', 'redo', '|',
        'heading', 'style', '|',
        'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', '|',
        'bold', 'italic', 'underline', 'strikethrough', 'subscript', 'superscript', '|',
        'link', 'insertImage', 'mediaEmbed', 'insertTable', 'blockQuote', 'htmlEmbed', '|',
        'bulletedList', 'numberedList', 'todoList', 'outdent', 'indent', '|',
        ...(showFullscreen ? ['fullscreen'] : [])
    ], [showFullscreen]);

    const { editorConfig } = useMemo(() => {
        if (!isLayoutReady) {
            return {};
        }
        return {
            editorConfig: {
                toolbar: {
                    items: toolbarItems || defaultToolbarItems,
                    shouldNotGroupWhenFull: true
                },
                plugins: [
                    Alignment, Autoformat, AutoImage, AutoLink, Autosave, Base64UploadAdapter, BlockQuote, Bold, Bookmark, Code, Emoji, Essentials, FindAndReplace, FontBackgroundColor, FontColor, FontFamily, FontSize, ...(showFullscreen ? [Fullscreen] : []), GeneralHtmlSupport, Heading, Highlight, HorizontalLine, HtmlComment, HtmlEmbed, ImageBlock, ImageCaption, ImageEditing, ImageInline, ImageInsert, ImageInsertViaUrl, ImageResize, ImageStyle, ImageTextAlternative, ImageToolbar, ImageUpload, ImageUtils, Indent, IndentBlock, Italic, Link, LinkImage, List, ListProperties, Markdown, MediaEmbed, Mention, PageBreak, Paragraph, PasteFromMarkdownExperimental, PasteFromOffice, RemoveFormat, ShowBlocks, SourceEditing, SpecialCharacters, SpecialCharactersArrows, SpecialCharactersCurrency, SpecialCharactersEssentials, SpecialCharactersLatin, SpecialCharactersMathematical, SpecialCharactersText, Strikethrough, Style, Subscript, Superscript, Table, TableCaption, TableCellProperties, TableColumnResize, TableProperties, TableToolbar, TextPartLanguage, TextTransformation, Title, TodoList, Underline, ...(effectiveShowWordCount ? [WordCount] : [])
                ],
                fontFamily: { supportAllValues: true },
                fontSize: { options: [10, 12, 14, 'default', 18, 20, 22], supportAllValues: true },
                ...(showFullscreen ? { fullscreen: { onEnterCallback: container => container.classList.add( 'editor-container', 'editor-container_classic-editor', 'editor-container_include-style', ...(effectiveShowWordCount ? ['editor-container_include-word-count'] : []), 'editor-container_include-fullscreen', 'main-container' ) } } : {}),
                heading: { options: [ { model: 'paragraph', title: 'Paragraph', class: 'ck-heading_paragraph' }, { model: 'heading1', view: 'h1', title: 'Heading 1', class: 'ck-heading_heading1' }, { model: 'heading2', view: 'h2', title: 'Heading 2', class: 'ck-heading_heading2' }, { model: 'heading3', view: 'h3', title: 'Heading 3', class: 'ck-heading_heading3' }, { model: 'heading4', view: 'h4', title: 'Heading 4', class: 'ck-heading_heading4' }, { model: 'heading5', view: 'h5', title: 'Heading 5', class: 'ck-heading_heading5' }, { model: 'heading6', view: 'h6', title: 'Heading 6', class: 'ck-heading_heading6' } ] },
                htmlSupport: { allow: [ { name: /^.*$/, styles: true, attributes: true, classes: true } ] },
                image: { toolbar: [ 'toggleImageCaption', 'imageTextAlternative', '|', 'imageStyle:inline', 'imageStyle:wrapText', 'imageStyle:breakText', '|', 'resizeImage' ] },
                licenseKey,
                link: { addTargetToExternalLinks: true, defaultProtocol: 'https://', decorators: { toggleDownloadable: { mode: 'manual', label: 'Downloadable', attributes: { download: 'file' } } } },
                list: { properties: { styles: true, startIndex: true, reversed: true } },
                mention: { feeds: [ { marker: '@', feed: [ ] } ] },
                menuBar: { isVisible: effectiveShowMenuBar },
                placeholder,
                style: { definitions: [ { name: 'Article category', element: 'h3', classes: ['category'] }, { name: 'Title', element: 'h2', classes: ['document-title'] }, { name: 'Subtitle', element: 'h3', classes: ['document-subtitle'] }, { name: 'Info box', element: 'p', classes: ['info-box'] }, { name: 'CTA Link Primary', element: 'a', classes: ['button', 'button--green'] }, { name: 'CTA Link Secondary', element: 'a', classes: ['button', 'button--black'] }, { name: 'Marker', element: 'span', classes: ['marker'] }, { name: 'Spoiler', element: 'span', classes: ['spoiler'] } ] },
                table: { contentToolbar: ['tableColumn', 'tableRow', 'mergeTableCells', 'tableProperties', 'tableCellProperties'] },
                readOnly: readOnly
            }
        };
    }, [ isLayoutReady, licenseKey, placeholder, effectiveShowMenuBar, effectiveShowWordCount, showFullscreen, toolbarItems, defaultToolbarItems, readOnly ]);

    const containerStyle = { fontFamily: 'system-ui, -apple-system, sans-serif', width: width === 'auto' ? 'fit-content' : width, height: height, marginLeft: 'auto', marginRight: 'auto', ...style };
    const editorStyle = { minWidth: width === 'auto' ? '300px' : width, maxWidth: width === 'auto' ? '100%' : width, minHeight: height === 'auto' ? '200px' : height };

    return (
      <div className={`rich-text-editor-container ${className}`} style={containerStyle}>
          {effectiveShowExportButtons && (
            <div className="rich-text-editor__export-bar">
                <div className="rich-text-editor__export-label">Export Options:</div>
                <div className="rich-text-editor__export-buttons">
                    <button onClick={exportToTxt} className="rich-text-editor__export-btn rich-text-editor__export-btn--txt">Export TXT</button>
                    <button onClick={exportToSrt} className="rich-text-editor__export-btn rich-text-editor__export-btn--srt">Export SRT</button>
                    {onSaveToDb && (<button onClick={saveToDatabase} disabled={isExporting} className={`rich-text-editor__export-btn rich-text-editor__export-btn--db ${isExporting ? 'rich-text-editor__export-btn--disabled' : ''}`}>{isExporting ? 'Saving...' : 'Save to DB'}</button>)}
                </div>
            </div>
          )}

          {effectiveShowMenuBar && (<div ref={editorMenuBarRef} className="rich-text-editor__menu-bar"></div>)}

          <div className="editor-container editor-container_classic-editor editor-container_include-style" ref={editorContainerRef}>
              <div className="editor-container__editor" style={editorStyle}>
                  <div ref={editorRef}>
                      {editorConfig && (
                        <CKEditor
                          onReady={editor => {
                              setEditorInstance(editor);
                              editor.setData(initialContent);
                              if (readOnly) {
                                  editor.enableReadOnlyMode('external-read-only-lock');
                              }
                              if (effectiveShowWordCount && editorWordCountRef.current) {
                                  try { const wordCountPlugin = editor.plugins.get('WordCount'); if (wordCountPlugin && wordCountPlugin.wordCountContainer) { editorWordCountRef.current.appendChild(wordCountPlugin.wordCountContainer); } } catch (e) { console.warn('WordCount plugin not available or error attaching container:', e); }
                              }
                              try { if (editor.ui?.view?.menuBarView?.element) { editorMenuBarRef.current?.appendChild(editor.ui.view.menuBarView.element); } } catch (e) { console.warn('Error attaching menu bar:', e); }
                          }}
                          onAfterDestroy={() => {
                              setEditorInstance(null);
                              try { if (editorWordCountRef.current) { Array.from(editorWordCountRef.current.children).forEach(child => child.remove()); } if (editorMenuBarRef.current) { Array.from(editorMenuBarRef.current.children).forEach(child => child.remove()); } } catch (e) { console.warn('Error cleaning up editor elements:', e); }
                          }}
                          editor={ClassicEditor}
                          config={editorConfig}
                          onChange={handleEditorChange}
                        />
                      )}
                  </div>
              </div>
          </div>

          {effectiveShowWordCount && (<div className="editor_container__word-count" ref={editorWordCountRef}></div>)}
      </div>
    );
}