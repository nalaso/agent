<script>
  import { agentState, isSending } from "$lib/store";
  import { calculateTokens } from "$lib/token";
  import { Icons } from "../icons";
  import { emitMessage, socketListener } from "$lib/sockets";

  let messageInput = "";
  async function handleSendMessage() {
    const projectName = localStorage.getItem("selectedProject");
    const selectedModel = localStorage.getItem("selectedModel");
    const serachEngine = localStorage.getItem("selectedSearchEngine");

    if (!projectName) {
      alert("Please select a project first!");
      return;
    }
    if (!selectedModel) {
      alert("Please select a model first!");
      return;
    }

    if (messageInput.trim() !== "" && isSending) {
      $isSending = true;
      emitMessage("user-message", { 
        message: messageInput,
        base_model: selectedModel,
        project_name: projectName,
        search_engine: serachEngine,
      });
      messageInput = "";
    }
  }

  function setTokenSize(event) {
    const prompt = event.target.value;
    let tokens = calculateTokens(prompt);
    document.querySelector(".token-count").textContent = `${tokens}`;
  }
</script>

<div class="expandable-input relative">
  <textarea
    id="message-input"
    class="w-full p-4 font-medium focus:text-foreground rounded-xl outline-none h-28 pr-20 bg-secondary {$isSending ? 'cursor-not-allowed' : ''}"
    placeholder="Type your message..."
    disabled={$isSending}
    bind:value={messageInput}
    on:input={setTokenSize}
    on:keydown={(e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        handleSendMessage();
        document.querySelector('.token-count').textContent = 0;
      }
    }}
  ></textarea>

  <button 
    on:click={handleSendMessage}
    disabled={$isSending}
    class="absolute text-secondary bg-primary p-2 right-4 bottom-6 rounded-full {$isSending ? 'cursor-not-allowed' : ''}"
  >
  {@html Icons.CornerDownLeft} 
  </button>
  <p class="absolute text-tertiary p-2 right-4 top-2">
    <span class="token-count">0</span>
  </p>
</div>

<style>
  .expandable-input textarea {
    min-height: 60px;
    max-height: 200px;
    resize: none;
  }
</style>
