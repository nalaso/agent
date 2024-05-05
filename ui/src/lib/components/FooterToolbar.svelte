<script>
    import { agentState, isSending } from "$lib/store";
    import { onMount } from "svelte";
    import Seperator from "./ui/Seperator.svelte";
    import { toast } from "svelte-sonner";
    import { socketListener } from "$lib/sockets";

    let prevMonologue = null;
    let inference_time = 0;

    agentState.subscribe((value) => {
      if (value !== null && value.agent_is_active == false) {
        isSending.set(false);
      }
      if (value == null){
        inference_time = 0;
      }
    });

    function handleMonologueChange(value) {
        if(!value) return;
        if(value == "Writing code..." || value == "Agent has completed the task."){
            toast.success(value);
        }
        else if(value && value.includes("error")) {
            toast.error(value);
        } 
        else {
            toast.message(value);
        }
    }
  
    onMount(() => {
      socketListener("inference", function (data) {
        if(data['type'] == 'time') {
          inference_time = data["elapsed_time"];
        }
      });
      prevMonologue = $agentState?.internal_monologue;
    });
  
    $: if ($agentState?.internal_monologue !== prevMonologue) {
      handleMonologueChange($agentState?.internal_monologue);
      prevMonologue = $agentState?.internal_monologue;
    }
  </script>
  
  <div class="flex items-center justify-between text-xs pt-2 border-t-2">
    <!-- right -->
    <div class="flex items-center">
      <div class="relative group px-1.5 hover:bg-secondary rounded-md">
        <p>
          Monologue:
          <span class="text-foreground">Hover me</span>
        </p>
        <div
          class="absolute hidden group-hover:block -left-1 text-[13px] w-[400px] bg-monologue-background bottom-8 duration-300 p-3 rounded-md space-y-2 outline outline-monologue-outline z-20"
        >
          <p>Monologue:</p>
          <p class="text-foreground">
            {$agentState?.internal_monologue || "😴"}
          </p>
        </div>
      </div>
      <Seperator height={14} />
      <div class="relative px-1.5 rounded-md">
        <p>
          Agent status:
          {#if $agentState !== null}
            {#if $agentState.agent_is_active}
              <span class="text-green-500">Active</span>
            {:else}
              <span class="text-orange-600">Inactive</span>
            {/if}
          {:else}
            Deactive
          {/if}
        </p>
      </div>
      <Seperator height={14} />
      <div class="relative px-1.5 rounded-md">
        <p>
          Model Inference:
          <span class="text-orange-300">{inference_time} sec</span>
        </p>
      </div>
    </div>
  
    <div></div>
    <!-- left -->
    <div class="flex gap-5 items-center">
      <p>
        Temperature:
        <span class="text-foreground"> 0.6 </span>
      </p>
      <Seperator height={14} />
      <p>
        Max Tokens:
        <span class="text-foreground"> 2200 </span>
      </p>
      <Seperator height={14} />
      <p>
        Top P:
        <span class="text-foreground"> 0.4 </span>
      </p>
    </div>
  </div>