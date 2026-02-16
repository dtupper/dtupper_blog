---
title: The Best PC for VRChat
status: Active
description: 
tags: [vrchat, hardware]
last_updated: 2026-02-11
---

:::details[⚠️ Important Disclaimer ⚠️]

**None of this information is condoned by, reviewed by, or endorsed by VRChat.** I am not doing this as an employee of VRChat. I am not getting compensated for writing any of this, either by VRChat or by any other entity. This is me, as an independent Person, answering questions I get asked pretty often.

**Recommendations change over time.** Do not be surprised when you revisit this page 6 months from now and your build is no longer recognizable.

**I provide no warranty and no guarantee for the information I provide.** It is a task left to the reader to validate all information I provide. Despite that, I provide as many sources as I can. 

**If you find something that is incorrect or inaccurate, *tell me*, and I will correct it.** I am not a hardware authority, simply an enthusiast. I compile information from many sources and combine it here.

Finally, **I am not immune to personal bias.** I have preferences that may be reflected in the recommendations I make. When I notice them, I will let you know, but I will deliver my best knowledge regardless.

:::

# [ℹ️ **Click here to skip to the builds.**](#the-builds)

# [🛠️ Click here to skip to the tweaks.](#the-tweaks)

# da best pc for vrchat EVER

I frequently hear these questions across social media, the VRChat subreddit, various Discord servers, and within VRChat itself:

> "What is the best PC for VRChat? What should I buy? **How do I get the most frames?"**

In previous versions of this document, I focused on the **absolute best** setup available, regardless of cost.

I hoped that by explaining the reasoning behind part selection, readers could build their own systems. They could choose more affordable components while still maximizing their PC's performance potential.

However, I've discovered that many people either:

1. don't fully grasp the reasoning behind certain optimization choices, or
2. *don't want to read*

The first is understandable.

The second is more confusing. **you're spending thousands of dollars.** Read some words before you spend your hard-earned money.

So, this guide will focus on two main sections:

**Section 1: The Builds.** This section will provide three [PCPartPicker](https://pcpartpicker.com/) builds using parametric filters, in "Good," "Better," "Best" format.

**Section 2: The Logic.** This section will explain our part selection criteria. **Not the specific components, but the reasoning behind our filters and choices.** This distinction is crucial!

Put simply: **What Do I Buy**, followed by **Why Am I Buying This.**

There is a third section now focusing on what tweaks you should do to your system.

# Assumptions

Before we begin, let's cover some basic assumptions for this guide.

1. **You know how to build a PC.** We're not dealing with prebuilt machines here. While prebuilts can be decent, building your own PC almost always yields better results.
2. **You generally understand what computer parts do.** You don't need to be a Linux guru, but you should know the basics about CPUs, GPUs, and RAM.
3. **You want a desktop.** Desktops offer better cooling, rarely thermal throttle, have easy-to-find parts, and provide plenty of room for future upgrades.

Don't worry if you're unsure about assumptions 1 or 2 — YouTube has excellent PC building guides and component explanations. It's much simpler than you might think, similar to assembling a (very expensive) LEGO set.

If assumption 3 doesn't fit your needs, you *could* look for a laptop with similar specifications.

However,

<aside>

**⚠️  I strongly recommend *against* a laptop for VR and VRChat usage. ⚠️**

</aside>

A laptop with "equivalent" specs will typically perform at 50-70% of the desktop's level while costing 30-50% *more*.

That's a poor value proposition. Only choose a laptop if portability is an *absolute* *must*.

# The Builds

<aside>

**⏳ Last updated Feb 11, 2025.**

</aside>

Builds do not include costs for the OS. 

For all builds, case selection is aesthetic. Get any ATX case. I recommend at least a mid-tower, get a full tower for ease of building.

PCPartPicker will not list an accurate total price in some cases where parts aren’t available.

:::callout
⚠️ **Warning:** RAM prices are brutal. I don't know if they'll ever come down. God save our souls
:::

## 🥉 Good

[**The Build**](https://pcpartpicker.com/list/qC4Dh7)

This build prioritizes cost-to-power efficiency on the side of a lower investment. Sacrifices are made in order to ensure a low cost. Components are prioritized by lowest cost, with some filtering for trustworthy (bias warning!) manufacturers.

<aside>

⚠️ **Warning**

This build is centered around the AMD 5700X3D. This is a dead-end CPU and hard to find. You can sub in a 5800X3D, but even then, it's still a dead-end socket.

As such, even though this is still a good build, _I really can't recommend aiming for it._

</aside>

## 🥈 Better

[**The Build**](https://pcpartpicker.com/list/pYbvNz)

This build focuses more on maximizing some specs (like VRAM and L3 cache) that are vital for high performance in VRChat without hitting the top line too hard.

**This build centers around the AM5 socket 7800X3D.** It focuses on increasing available VRAM to 16GB, getting higher quality RAM with better timings, and ensuring parts overall do not bottleneck unnecessarily.

**If** you can get your hands on it, the Radeon 9070 XT is an *excellent* contender for this build. It has ample RAM at 16GB, and in [certain configurations](https://videocardz.com/newz/radeon-rx-9070-xt-outperforms-geforce-rtx-5080-in-cyberpunk-2077-and-3dmark-after-undervolting-3-3-ghz-clock-reached) outperforms the 5080 — which is *wild* at it’s price point.

Good luck getting one, though.

## 🥇 Best

[**The Build**](https://pcpartpicker.com/list/fjhMmC)

**This build completely ignores cost** as a factor, and focuses on the top-of-the-line components available to maximize your frames in VRChat. Each part has been hand selected.

### CPU

**This build centers around the AM5 socket 9800X3D.** 

It was selected over the 9950X3D due to a lack of availability for the 9950X3D, and [trusted benchmarkers](https://gamersnexus.net/cpus/amd-ryzen-9-9950x3d-cpu-review-benchmarks-vs-9800x3d-285k-9950x-more) noting that the 9950X3D’s use case is limited to those who game and also perform content creation (video editing). Benchmarks indicate that the performance gain of the 9950X3D over the 9800X3D is less than 3% in most cases, which is within error bars.

However, the 9950X3D may also be useful for those that find themselves heavily multi-tasking. If you run a lot of things in addition to VRChat, you can shove noncritical processes to the second CCD while allowing VRChat to run exclusively on the first.

The 9950X3D will also be useful if you create content for VRChat, such as worlds or avatars.

<aside>
🆕

As of Jan 28, 2026, **the 9850X3D is now the best choice for VRChat.** It’s got about a 7-8% lift over the 9800X3D thanks to an improved boost clock but not much else.

Watch Linus yap about it [here](https://www.youtube.com/watch?v=4Ps-JDyimJw).

The rest of this guide still applies. 

</aside>

### GPU

As of February 11th, 2026, obtaining the recommended nVidia Founder’s Edition 5090 at anything even remotely close to MSRP is *still impossible.* You can buy it, but you'll be shelling out 3000+ USD. (ask me how i know)

As such, if you make this build, do your best to get a GPU that maximizes VRAM, and then core clock. This means your candidate list looks like this:

1. nVidia 5090
2. nVidia 4090
3. AMD 7900XTX

All of these GPUs have 24GB or more VRAM, high core clocks, and excellent raster performance.

The 3090 is worth mentioning if you are dead-set on getting more VRAM, and you can find one for relatively cheap (1400 or less?). The 3090 is still very powerful — just *less powerful* than other GPUs out there. nVidia went through a pretty serious upgrade from the 3000 to 4000 series in terms of memory speed and bus width.

# The Logic

## CPU

Intel is dead, AMD is king.

The X3D line of AMD CPUs are labeled as such because they utilize a “3D Cache,” effectively a stack of fast memory mounted directly on the CPU.

This *extremely high speed* memory allows your CPU to buffer more instructions and handle data more efficiently, resulting in ridiculous performance gains over Intel.

Do not buy Intel CPUs right now. It would be a very poor choice.

## GPU

In short, maximize VRAM, maximize core clock, maximize raster performance.

GPUs are very hard to get a hold of these days.

**The problem is AI.**

No, this isn’t the author’s take on AI, but per [Tom’s Hardware](https://www.tomshardware.com/reviews/gpu-hierarchy,4388.html):

> AI is all the rage, commanding billions of dollars in sales. It accounted for nearly 90% of [Nvidia's record-setting $130 billion in annual revenue](https://www.tomshardware.com/pc-components/gpus/nvidia-enjoys-usd130b-annual-earnings-despite-gaming-segment-supply-constraints) for last fiscal year. **Gaming was just under 9% of the total.**
> 

In other words, you, the GAMER, are no longer the hottest one in the room. If you randomly sampled 10 GPUs sold today, 9 of them would be destined for a data center so that someone can talk to a search assistant, write code, or generate an anime girl.

sigh, first it was bitcoin mining, now its AI. [its so over, gamers...](https://www.youtube.com/watch?v=s-09gNDsPzQ)

Anyways, gaming GPU supply goes down, and demand is just as high as it’s ever been — so price shoots up. Yay.

As such, get whatever GPU you can that has the most VRAM, has the highest core clock, and is in the latest generations.

Thankfully, this problem mostly affects mid-range and high-end GPUs. If you’re building a lower end machine, affordable GPUs are pretty easy to get.

If you’re in the market for a 5090, 4090, 7900XTX, or 9070 XT: lol, lmao. Good luck.

<aside>

**Creators:** If you’re building worlds, [Bakery](https://assetstore.unity.com/packages/tools/level-design/bakery-gpu-lightmapper-122218), the “standard” for high quality light bakes, only works on nVidia.

</aside>

## RAM

Minimize latency (CL30), maximize transfer rate (6000), maximize capacity (32GB+).

Beyond that, minimize your cost, choose your favorite vendor, and put some RGBs on it if you want idk

## SSD

PCIE 5.0 is here, and damn, it’s fast. If you can get it, do so. 

Don’t run VRChat or your cache off a mechanical drive. Please. Or your OS. Or anything, really. SSDs are cheap, damn it, just get one.

## PSU

**Never, ever cheap out on your PSU.**

Don’t skimp. Spend some money. Get something with good efficiency, good ratings, and from a known brand. I swear by SeaSonic. 

PCPartPicker will make sure you don’t select something that’s too low, but generally, with headroom at peak load:

- Your CPU will eat 150-200W
- Your GPU will eat anywhere from 200 to 650W
- The rest of your components will sip ~50-100W

For Good and Better, 650 to 800W is fine. For Best, start at 1000W.

# The Tweaks

There’s a few things you should do in order to maximize performance.

### 7950 / 9950X3D Note

If you’re running these CPUs, you have an extra CCD to contend with. You do not want processes to talk "across" this CCD gap -- you will incur latency & thus lose frames.

VRChat handles this automagically. If you want to be super sure, `--affinity=FFFF` locks VRChat to the first 16 logical cores. [Look at our docs](https://docs.vrchat.com/docs/launch-options#amd-inter-ccx-latency-and-core-affinity) for more information on that command.

If you want to min-max: Look into using Process Lasso to shove things onto the second CCD so they don’t take up CPU time that VRChat could be using instead. Candidates include:

- Browser
- Discord
- VRCX
- XSOverlay / OVR Toolkit, other overlays
- OBS

Don’t put Steam or SteamVR onto the second CCD. Processes inherit their parents’ CPU sets & limitations unless overridden manually. Plus, that may affect other non-VRChat games.

### AMD Ryzen Master

Mixed feedback.

My own experience was pretty painful — it got “out of sync” with my BIOS settings. It resulted in some terrible CPU issues, like VRChat being locked to a single core.

If you use Ryzen Master, use it exclusively. Do not adjust settings in the BIOS. If you get “out of sync”, reapply the same tunings  in RM that you did in the BIOS.

I have read that RM has serious issues with dual-boot systems, so if you’re doing that, do NOT use RM.

## BIOS Settings

1. Enable XMP and ensure your memory is running at the proper speed.
    1. Don’t forget this step. 
    2. Try XMP II first, then fall back to XMP I if you encounter instability.
2. [Consider overclocking the CPU.](https://www.youtube.com/watch?v=4Ukf__UGTOw)
    1. The 9800X3D overclocks cleanly, and even with a half-decent air cooler rarely breaks 70C.
    2. Even just the basic 200MHz boost via PBO can get you a good amount of headwind.
    3. Look into undervolting via PBO, too.
3. I can't recommend overclocking your memory. Don't do it.
4. Make sure Resizable BAR is on.

## Windows 11

**Never use upgrade installs.** Avoid installing too much extra crap.

Make sure you’re up to date. That’s it.

If you’re nitpicky, you might want to run [Win11Debloat](https://github.com/Raphire/Win11Debloat), but this won’t do too much.

:::callout
⚠️ **Bad Windows Update Alert** - 11 Feb 2026
:::

In typical Microsoft fashion, a recent Windows update has killed performance. nVidia confirms it [here.](https://www.xda-developers.com/nvidia-confirms-windows-11-january-update-causes-frame-drops-artifacting/)

Kill it by running the following command in Command Prompt or Powershell, then restart your PC. 

```powershell
wusa.exe /uninstall /KB:5074109
```

You may have to do this multiple times if the little bastard reinstalls itself.

## GPU Drivers

### nVidia

Use [**NVCleanstall**](https://www.techpowerup.com/download/techpowerup-nvcleanstall/). This is *critical* — do not simply install over older versions.

I prefer to use the latest Studio version for better stability.

### AMD

Keep drivers up to date.

Nothing as well known or well-used like NVCleanstall exists for AMD, but I did find [this](https://github.com/GSDragoon/RadeonSoftwareSlimmer), so idk, give it a shot if you really want to

## Connecting your Headset

I personally strongly prefer direct-to-GPU tethered headsets (Beyond, Index, etc) because you do not need to worry about battery life, network latency, bandwidth, compression, color space squashing, etc.

However, new headsets such as the Steam Frame make wireless VR very compelling. Weight is coming down, comfort is going up, and we're escaping the bonds of Meta. Finally.

Either way, if you are using wireless either out of necessity or because you prefer it:

1. Ensure you have a high-quality, *ideally dedicated* WiFi 6 network for your headset
    1. I’ve done this in the past by using a second router in Access Point (AP) mode, connecting my ethernet to it, then connecting another ethernet to my PC
    2. Then, in the AP settings, create a new WiFi network dedicated to the headset
    3. If you’ve got a well set-up network with 2.5GB+ ethernet to your PC and good quality WiFi APs (Ubiquiti U7 Pros are overkill but they’re so nice), you might be able to pull this off on your base network.
    4. This won't apply if you have/get a Steam Frame, you get the dongle
2. Use Steam Link or Virtual Desktop
    1. They’re both great. Steam Link has some advantages, VD has others. 
        1. Steam Link
            1. If you have eye tracking, Steam Link uses foveated encoding (*not rendering*) to lower the bandwidth requirements and reduce encoding load
            2. It requires very little configuration
            3. It’s built into SteamVR, free, and Just Works™
            4. It's gonna get lots of nice new updates now that the Frame is on the way
        2. Virtual Desktop
            1. Virtual Desktop does a lot of cool tricks to maximize quality
            2. It’s very configurable and tweakable
            3. You can use the spare CPU on your Quest headset to sharpen the image, potentially improving image quality (but.. you also might not like the effect)
            4. The VD dev is super active, reactive to feedback, and very helpful. 25 bucks is nothing compared to the value his work delivers, pay the man
        3. Both work with VRCFT, if you’ve got a Quest Pro or another eye/face tracking wireless HMD.
3. Do *not* use Quest Link, unless you have no other choice.
    1. It hasn’t gotten meaningful updates in years
    2. The quality isn’t great
    3. It isn’t configurable at all
    4. You have to do [some shenanigans](https://x.com/whatdahopper/status/1754748582240920014) to turn off Asynchronous Timewarp (and you really, really should)        
    5. … but if wireless isn’t an option, and all you have is a Quest, then wired Quest Link might be your only choice. bless your heart.

## VRChat, SteamVR, etc Settings

Go follow [EchoTheNeko’s guide](https://docs.google.com/document/d/1BdyWxQhFoRkJVfsLvcPNHgvL-esUEE76WbDfguOVbMg/edit?tab=t.0). It’s good.

In particular:

1. **TURN OFF MOTION SMOOTHING.** You should essentially *never* use motion smoothing.
    1. Not only does it look bad, it has few (if any) benefits.
    2. It also causes crashes on current (May 8 2025) drivers for AMD RX 9000 series GPUs.
2. **Turn off AA in VRChat** if you’re using a high-resolution headset (Bigscreen Beyond).
3. **Consider running at lower supersampling resolutions.** I usually run at 100% these days!
4. ⚠️ **Make sure SteamVR Motion Smoothing is OFF.**
    1. Despite being intended as a motion sickness preventative, it often *causes* motion sickness and disrupts your visuals in a serious way, making your screen look plain broken.
    2. Oculus does this too in Quest Link. It’s called ASW and it’s a pain to turn off.
        1. (Why are you using Quest Link??????)
    3. I don’t know why companies still think this is a good way to prevent motion sickness.