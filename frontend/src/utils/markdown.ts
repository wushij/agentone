import MarkdownIt from 'markdown-it'
import hljs from 'highlight.js'

function highlightCode(str: string, lang: string): string {
  if (lang && hljs.getLanguage(lang)) {
    try {
      return `<pre><code class="hljs language-${lang}">${hljs.highlight(str, { language: lang }).value}</code></pre>`
    } catch {
      /* fall through */
    }
  }
  const escaped = str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
  return `<pre><code class="hljs">${escaped}</code></pre>`
}

const md = new MarkdownIt({
  html: false,
  linkify: true,
  breaks: true,
  highlight: highlightCode
})

export function renderMarkdown(content: string): string {
  if (!content.trim()) return ''
  return md.render(content)
}
