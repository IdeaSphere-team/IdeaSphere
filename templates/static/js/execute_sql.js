document.addEventListener('DOMContentLoaded', () => {
    // 将 editor 提升到全局作用域
    window.editor = document.getElementById('codeEditor');
    const submitButton = document.getElementById('submit-sql-statement-to-backend');

    editor.contentEditable = 'true';
    editor.className = 'language-sql';

    let highlightTimeout;
    let currentRange; // 直接保存完整Range对象

    // 事件监听优化
    editor.addEventListener('input', (e) => {
        // 保存当前选区相对于整个文本的偏移量
        const selection = window.getSelection();
        if (selection.rangeCount > 0) {
            const range = selection.getRangeAt(0);
            const preRange = range.cloneRange();
            preRange.selectNodeContents(editor);
            preRange.setEnd(range.startContainer, range.startOffset);
            currentRange = {
                start: preRange.toString().length,
                end: preRange.toString().length + range.toString().length
            };
        }
        debounceHighlight();
    });

    const highlightWithCursor = () => {
        // 1. 保存当前Range
        const savedRange = currentRange;

        // 2. 执行高亮
        const highlighted = hljs.highlight(editor.textContent, {language: 'sql'});
        editor.innerHTML = highlighted.value;
        editor.contentEditable = 'true'; // 强制保留可编辑属性

        // 3. 恢复Range
        if (savedRange) {
            const newRange = document.createRange();
            const start = findNodeAtOffset(editor, savedRange.start);
            const end = findNodeAtOffset(editor, savedRange.end);

            if (start.node && end.node) {
                try {
                    newRange.setStart(start.node, start.offset);
                    newRange.setEnd(end.node, end.offset);
                    const selection = window.getSelection();
                    selection.removeAllRanges();
                    selection.addRange(newRange);
                } catch (e) {
                    console.log('Cursor restore failed:', e);
                    // 失败时将光标定位到编辑器末尾
                    const range = document.createRange();
                    range.selectNodeContents(editor);
                    range.collapse(false);
                    selection.removeAllRanges();
                    selection.addRange(range);
                }
            }

        }
    };

    // 防抖函数
    const debounceHighlight = () => {
        clearTimeout(highlightTimeout);
        highlightTimeout = setTimeout(highlightWithCursor, 300);
    };

    // 新增：根据偏移量找到具体文本节点
    const findNodeAtOffset = (container, targetOffset) => {
        let total = 0;
        const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT, null, false);
        let lastNode = null;

        while (true) {
            const node = walker.nextNode();
            if (!node) break;

            const length = node.textContent.length;
            if (total <= targetOffset && total + length >= targetOffset) {
                return {node, offset: targetOffset - total};
            }
            total += length;
            lastNode = node;
        }

        // 处理超出范围的情况
        return lastNode ?
            {node: lastNode, offset: lastNode.textContent.length} :
            {node: container, offset: 0};
    };


    // 初始化高亮
    highlightWithCursor();
});
