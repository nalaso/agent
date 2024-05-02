<script>
  import { onDestroy, onMount } from "svelte";
  import ControlPanel from "$lib/components/ControlPanel.svelte";
  import MessageContainer from "$lib/components/MessageContainer.svelte";
  import MessageInput from "$lib/components/MessageInput.svelte";
  import BrowserWidget from "$lib/components/BrowserWidget.svelte";
  import TerminalWidget from "$lib/components/TerminalWidget.svelte";
  import * as Resizable from "$lib/components/ui/resizable/index.js";
  import FooterToolbar from "$lib/components/FooterToolbar.svelte";

  import { checkInternetStatus, checkServerStatus } from "$lib/api";
  import { initializeSockets, destroySockets } from "$lib/sockets";
  import { serverStatus } from "$lib/store";
  import EditorWidget from "../lib/components/EditorWidget.svelte";

  let resizeEnabled =
    localStorage.getItem("resize") &&
    localStorage.getItem("resize") === "enable";
  
  onMount(() => {
    const load = async () => {
      await checkInternetStatus();
      if(!await checkServerStatus()) {
        toast.error("Failed to connect to server");
        return;
      }

      serverStatus.set(true);
      console.log("Server is online");
      await initializeSockets();
      console.log("Sockets initialized");
    };
    load();
  });

  onDestroy(() => {
    destroySockets()
  });
</script>

<div class="flex h-full flex-col flex-1 p-3 overflow-hidden">
  <ControlPanel />

  <div class="flex flex-1 max-w-[95vw] overflow-x-auto">
    <Resizable.PaneGroup direction="horizontal" class={"min-w-[140vw] snap-mandatory snap-x"} autoSaveId="default">
      <Resizable.Pane defaultSize={40} class="snap-center">
        <div class="flex flex-col gap-2 w-full h-full pr-4">
          <MessageContainer />
          <MessageInput />
        </div>
      </Resizable.Pane>
      {#if resizeEnabled}
        <Resizable.Handle />
      {/if}
      <Resizable.Pane defaultSize={40} class="snap-center">
        <Resizable.PaneGroup direction="vertical">
          <Resizable.Pane defaultSize={50}>
            <div class="flex h-full items-center justify-center p-2">
              <BrowserWidget />
            </div>
          </Resizable.Pane>
          {#if resizeEnabled}
            <Resizable.Handle />
          {/if}
          <Resizable.Pane defaultSize={50}>
            <div class="flex h-full items-center justify-center p-2">
              <TerminalWidget />
            </div>
          </Resizable.Pane>
        </Resizable.PaneGroup>
      </Resizable.Pane>
      {#if resizeEnabled }
        <Resizable.Handle />
      {/if}
      <Resizable.Pane defaultSize={50} class="snap-center">
        <div class="flex flex-col gap-2 w-full h-full pr-4 p-2">
          <EditorWidget />
        </div>
      </Resizable.Pane>
    </Resizable.PaneGroup>
    </div>
    <FooterToolbar />
</div>