(() => {
  if (!document.querySelector('[data-chat-widget]')) {
    document.body.insertAdjacentHTML('beforeend', `
      <aside class="chat-widget" data-chat-widget aria-label="Assistente virtual do Squad B">
        <section class="chat-panel" aria-label="Conversa com o assistente">
          <header class="chat-header">
            <div><strong>Assistente Squad B</strong><small data-chat-status>Assistente do Squad B</small></div>
            <button class="chat-close" data-chat-close type="button" aria-label="Fechar chat">&times;</button>
          </header>
          <div class="chat-messages" data-chat-messages>
            <div class="chat-message chat-message--bot">Olá, sou a MarIA, a inteligência artificial do Squad B! Estou aqui para ajudar você com suas dúvidas.</div>
          </div>
          <form class="chat-form" data-chat-form>
            <input data-chat-input type="text" maxlength="2000" placeholder="Pergunte sobre o site..." aria-label="Mensagem" required>
            <button type="submit">Enviar</button>
          </form>
        </section>
        <button class="chat-toggle" data-chat-toggle type="button" aria-label="Abrir assistente">✦</button>
      </aside>`);
  }

  const widget = document.querySelector('[data-chat-widget]');

  const toggle = widget.querySelector('[data-chat-toggle]');
  const close = widget.querySelector('[data-chat-close]');
  const form = widget.querySelector('[data-chat-form]');
  const input = widget.querySelector('[data-chat-input]');
  const messages = widget.querySelector('[data-chat-messages]');
  const status = widget.querySelector('[data-chat-status]');

  const setThinking = (thinking) => {
    const existing = messages.querySelector('[data-thinking]');
    if (thinking && !existing) {
      messages.insertAdjacentHTML('beforeend', '<div class="chat-message chat-message--bot chat-thinking" data-thinking aria-label="A MarIA está pensando"><span></span><span></span><span></span></div>');
      messages.scrollTop = messages.scrollHeight;
    }
    if (!thinking && existing) existing.remove();
  };

  const addMessage = (text, author) => {
    const message = document.createElement('div');
    message.className = `chat-message chat-message--${author}`;
    message.textContent = text;
    messages.appendChild(message);
    messages.scrollTop = messages.scrollHeight;
  };

  const setOpen = (open) => {
    widget.classList.toggle('is-open', open);
    if (open) input.focus();
  };

  toggle.addEventListener('click', () => setOpen(!widget.classList.contains('is-open')));
  close.addEventListener('click', () => setOpen(false));

  form.addEventListener('submit', async (event) => {
    event.preventDefault();
    const message = input.value.trim();
    if (!message) return;
    addMessage(message, 'user');
    input.value = '';
    input.disabled = true;
    status.textContent = 'MarIA está pensando...';
    setThinking(true);

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 30000);
      const result = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ message }),
        signal: controller.signal,
      });
      clearTimeout(timeout);
      const data = await result.json();
      if (!result.ok) throw new Error(data.error || 'Não foi possível responder.');
      setThinking(false);
      addMessage(data.reply, 'bot');
    } catch (error) {
      setThinking(false);
      addMessage(error.name === 'AbortError' ? 'A resposta demorou mais que o esperado. Tente novamente.' : error.message, 'bot');
    } finally {
      input.disabled = false;
      status.textContent = 'Assistente do Squad B';
      input.focus();
    }
  });
})();
