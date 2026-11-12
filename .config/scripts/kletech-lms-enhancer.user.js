// ==UserScript==
// @name         KLE Tech LMS Video Enhancer & Subtitles
// @namespace    https://learn.kletech.ac.in/
// @version      2.0
// @description  Deep iframe-piercing YouTube keybinds, timeline scrubber unlocks, sleek Wallust HUD, and Subtitle/CC engine for KLE Tech Moodle & H5P lecture videos.
// @author       Katana
// @match        https://learn.kletech.ac.in/*
// @include      https://learn.kletech.ac.in/*
// @grant        none
// @run-at       document-start
// @allFrames    true
// ==/UserScript==

(function () {
    'use strict';

    console.log('[LMS Enhancer 2.0] Script loaded in:', window.location.href);

    const CSS_STYLES = `
        .lms-player-wrapper {
            position: relative !important;
        }
        .lms-player-wrapper:fullscreen {
            background: #000000 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            width: 100vw !important;
            height: 100vh !important;
        }
        .lms-player-wrapper:fullscreen video {
            max-width: 100% !important;
            max-height: 100% !important;
            width: 100% !important;
            height: 100% !important;
            object-fit: contain !important;
        }
        .lms-hud {
            position: absolute !important;
            top: 50% !important;
            left: 50% !important;
            transform: translate(-50%, -50%) !important;
            background: rgba(15, 16, 16, 0.92) !important;
            border: 2px solid #887D75 !important;
            color: #91A5C1 !important;
            font-family: 'JetBrainsMono Nerd Font Propo', 'JetBrainsMono Nerd Font', monospace, sans-serif !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            padding: 10px 22px !important;
            border-radius: 0px !important;
            pointer-events: none !important;
            z-index: 2147483647 !important;
            opacity: 0 !important;
            transition: opacity 0.15s ease-in-out !important;
            box-shadow: 0 6px 24px rgba(0, 0, 0, 0.7) !important;
            display: flex !important;
            align-items: center !important;
            gap: 10px !important;
            user-select: none !important;
        }
        .lms-hud.show {
            opacity: 1 !important;
        }
        .lms-cc-container {
            position: absolute !important;
            bottom: 56px !important;
            left: 50% !important;
            transform: translateX(-50%) !important;
            max-width: 88% !important;
            text-align: center !important;
            pointer-events: none !important;
            z-index: 2147483646 !important;
        }
        .lms-cc-text {
            background: rgba(15, 16, 16, 0.90) !important;
            color: #FFFFFF !important;
            font-family: 'JetBrainsMono Nerd Font Propo', 'Noto Sans', 'Inter', sans-serif !important;
            font-size: 21px !important;
            font-weight: 600 !important;
            padding: 6px 14px !important;
            border-radius: 0px !important;
            border: 1px solid rgba(136, 125, 117, 0.5) !important;
            line-height: 1.4 !important;
            display: inline-block !important;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.9) !important;
            box-decoration-break: clone !important;
            -webkit-box-decoration-break: clone !important;
        }
        .lms-top-toolbar {
            position: absolute !important;
            top: 10px !important;
            left: 10px !important;
            display: flex !important;
            gap: 6px !important;
            z-index: 2147483645 !important;
            opacity: 0.55 !important;
            transition: opacity 0.2s ease-in-out !important;
        }
        .lms-top-toolbar:hover,
        .lms-player-wrapper:hover .lms-top-toolbar {
            opacity: 1 !important;
        }
        .lms-btn {
            background: #0F1010 !important;
            border: 1px solid #887D75 !important;
            color: #91A5C1 !important;
            font-family: 'JetBrainsMono Nerd Font Propo', monospace !important;
            font-size: 11px !important;
            font-weight: 600 !important;
            padding: 5px 9px !important;
            cursor: pointer !important;
            border-radius: 0px !important;
            transition: all 0.15s ease !important;
            box-shadow: 0 2px 8px rgba(0,0,0,0.5) !important;
        }
        .lms-btn:hover {
            background: #373736 !important;
            color: #B3BCCA !important;
            border-color: #91A5C1 !important;
        }
        .lms-btn.active {
            background: #887D75 !important;
            color: #0F1010 !important;
            border-color: #887D75 !important;
            font-weight: 700 !important;
        }
    `;

    const SPEEDS = [0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 1.75, 2.0, 2.5, 3.0];
    let hudTimeout = null;
    let activeVideo = null;
    let ccFontSize = 21;

    function ensureStyles(doc) {
        if (!doc || !doc.head) return;
        if (doc.getElementById('lms-enhancer-styles')) return;
        const style = doc.createElement('style');
        style.id = 'lms-enhancer-styles';
        style.textContent = CSS_STYLES;
        doc.head.appendChild(style);
    }

    function showHUD(video, text) {
        if (!video) return;
        const wrapper = video.closest('.lms-player-wrapper') || video.parentElement;
        if (!wrapper) return;
        let hud = wrapper.querySelector('.lms-hud');
        if (!hud) {
            hud = video.ownerDocument.createElement('div');
            hud.className = 'lms-hud';
            wrapper.appendChild(hud);
        }
        hud.textContent = text;
        hud.classList.add('show');
        if (hudTimeout) clearTimeout(hudTimeout);
        hudTimeout = setTimeout(() => hud.classList.remove('show'), 750);
    }

    function parseSubtitles(text) {
        const cues = [];
        const lines = text.trim().replace(/\r\n/g, '\n').replace(/\r/g, '\n').split('\n');
        let i = 0;

        function timeToSeconds(tStr) {
            const parts = tStr.trim().split(':');
            let s = 0;
            if (parts.length === 3) {
                s = parseFloat(parts[0]) * 3600 + parseFloat(parts[1]) * 60 + parseFloat(parts[2].replace(',', '.'));
            } else if (parts.length === 2) {
                s = parseFloat(parts[0]) * 60 + parseFloat(parts[1].replace(',', '.'));
            }
            return s;
        }

        while (i < lines.length) {
            let line = lines[i].trim();
            if (line.includes('-->')) {
                const [startStr, endStr] = line.split('-->');
                const start = timeToSeconds(startStr);
                const end = timeToSeconds(endStr);
                i++;
                let cueText = [];
                while (i < lines.length && lines[i].trim() !== '') {
                    cueText.push(lines[i].trim());
                    i++;
                }
                cues.push({ start, end, text: cueText.join(' ') });
            }
            i++;
        }
        return cues;
    }

    function copyToClipboard(text, doc) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(text).catch(() => fallbackCopy(text, doc));
        } else {
            fallbackCopy(text, doc);
        }
    }

    function fallbackCopy(text, doc) {
        const ta = doc.createElement('textarea');
        ta.value = text;
        ta.style.position = 'fixed';
        ta.style.opacity = '0';
        doc.body.appendChild(ta);
        ta.focus();
        ta.select();
        try { doc.execCommand('copy'); } catch (e) {}
        doc.body.removeChild(ta);
    }

    function setupVideo(video) {
        if (video.dataset.lmsEnhanced) return;
        video.dataset.lmsEnhanced = "true";

        const doc = video.ownerDocument;
        ensureStyles(doc);

        console.log('[LMS Enhancer 2.0] Hooking video element in doc:', doc.title || doc.location.href, video);

        if (!activeVideo) activeVideo = video;
        video.addEventListener('play', () => { activeVideo = video; });
        video.addEventListener('click', () => { activeVideo = video; });
        video.addEventListener('focus', () => { activeVideo = video; });
        video.addEventListener('mouseenter', () => { activeVideo = video; });

        // Identify optimal container wrapper (H5P video wrapper or fallback)
        let wrapper = video.closest('.h5p-video-wrapper, .h5p-interactive-video, .video-js') || video.parentElement;
        if (!wrapper.classList.contains('lms-player-wrapper')) {
            wrapper.classList.add('lms-player-wrapper');
        }

        // Subtitle Elements
        let ccContainer = doc.createElement('div');
        ccContainer.className = 'lms-cc-container';
        let ccText = doc.createElement('div');
        ccText.className = 'lms-cc-text';
        ccText.style.fontSize = `${ccFontSize}px`;
        ccText.style.display = 'none';
        ccContainer.appendChild(ccText);
        wrapper.appendChild(ccContainer);

        let activeCues = [];
        let ccEnabled = false;

        video._toggleCC = function () {
            ccEnabled = !ccEnabled;
            ccBtn.classList.toggle('active', ccEnabled);
            showHUD(video, ccEnabled ? '💬 CC: ON' : '💬 CC: OFF');
            if (!ccEnabled) ccText.style.display = 'none';
        };

        video._changeCCFontSize = function (delta) {
            ccFontSize = Math.max(12, Math.min(42, ccFontSize + delta));
            ccText.style.fontSize = `${ccFontSize}px`;
            showHUD(video, `🔤 CC Size: ${ccFontSize}px`);
        };

        video.addEventListener('timeupdate', () => {
            if (!ccEnabled || activeCues.length === 0) {
                ccText.style.display = 'none';
                return;
            }
            const cur = video.currentTime;
            const currentCue = activeCues.find(c => cur >= c.start && cur <= c.end);
            if (currentCue) {
                ccText.textContent = currentCue.text;
                ccText.style.display = 'inline-block';
            } else {
                ccText.style.display = 'none';
            }
        });

        // Top Toolbar
        const toolbar = doc.createElement('div');
        toolbar.className = 'lms-top-toolbar';

        // 1. Toggle CC Button
        const ccBtn = doc.createElement('button');
        ccBtn.className = 'lms-btn';
        ccBtn.textContent = 'CC [c]';
        ccBtn.title = 'Toggle Subtitles (or press c)';
        ccBtn.onclick = (e) => {
            e.stopPropagation();
            video._toggleCC();
        };

        // 2. Load Subtitles File Button
        const fileInput = doc.createElement('input');
        fileInput.type = 'file';
        fileInput.accept = '.vtt,.srt';
        fileInput.style.display = 'none';
        fileInput.onchange = (e) => {
            const file = e.target.files[0];
            if (!file) return;
            const reader = new FileReader();
            reader.onload = (re) => {
                activeCues = parseSubtitles(re.target.result);
                ccEnabled = true;
                ccBtn.classList.add('active');
                showHUD(video, `✅ Loaded ${activeCues.length} cues`);
            };
            reader.readAsText(file);
        };

        const loadBtn = doc.createElement('button');
        loadBtn.className = 'lms-btn';
        loadBtn.textContent = '📂 Load CC';
        loadBtn.title = 'Load .vtt or .srt subtitle file from disk';
        loadBtn.onclick = (e) => {
            e.stopPropagation();
            fileInput.click();
        };

        // 3. Paste Subtitle Text / URL
        const pasteBtn = doc.createElement('button');
        pasteBtn.className = 'lms-btn';
        pasteBtn.textContent = '🔗 Paste CC';
        pasteBtn.title = 'Paste subtitle text or direct URL';
        pasteBtn.onclick = async (e) => {
            e.stopPropagation();
            const text = prompt('Paste .srt / .vtt subtitle content or direct raw URL:');
            if (!text) return;
            if (text.startsWith('http')) {
                try {
                    const resp = await fetch(text);
                    const vtt = await resp.text();
                    activeCues = parseSubtitles(vtt);
                    ccEnabled = true;
                    ccBtn.classList.add('active');
                    showHUD(video, `✅ Loaded ${activeCues.length} cues from URL`);
                } catch (err) {
                    alert('Failed to fetch subtitle URL: ' + err);
                }
            } else {
                activeCues = parseSubtitles(text);
                ccEnabled = true;
                ccBtn.classList.add('active');
                showHUD(video, `✅ Loaded ${activeCues.length} cues`);
            }
        };

        // 4. Copy Direct Stream URL
        const streamBtn = doc.createElement('button');
        streamBtn.className = 'lms-btn';
        streamBtn.textContent = '📋 Stream URL';
        streamBtn.title = 'Copy raw video stream URL for Whisper transcription or local playback';
        streamBtn.onclick = (e) => {
            e.stopPropagation();
            const url = video.currentSrc || video.src || (video.querySelector('source') ? video.querySelector('source').src : '');
            if (url) {
                copyToClipboard(url, doc);
                showHUD(video, '📋 Stream URL Copied');
            } else {
                showHUD(video, '⚠️ Stream URL not found');
            }
        };

        toolbar.appendChild(ccBtn);
        toolbar.appendChild(loadBtn);
        toolbar.appendChild(pasteBtn);
        toolbar.appendChild(streamBtn);
        wrapper.appendChild(toolbar);
        wrapper.appendChild(fileInput);
    }

    // Traverse all accessible same-origin & about:blank documents (top + iframes)
    function getAllDocuments() {
        const docs = [];
        function collect(doc) {
            if (!doc || docs.includes(doc)) return;
            docs.push(doc);
            try {
                const iframes = doc.querySelectorAll('iframe');
                for (const iframe of iframes) {
                    try {
                        iframe.setAttribute('allowfullscreen', 'true');
                        iframe.setAttribute('webkitallowfullscreen', 'true');
                        iframe.setAttribute('mozallowfullscreen', 'true');
                        iframe.setAttribute('allow', 'fullscreen *; autoplay *; encrypted-media *');

                        const cDoc = iframe.contentDocument;
                        if (cDoc) collect(cDoc);
                    } catch (e) {
                        // Protected cross-origin iframe
                    }
                }
            } catch (e) {}
        }
        collect(document);
        return docs;
    }

    function getTargetVideo() {
        if (activeVideo && activeVideo.isConnected) return activeVideo;
        const allDocs = getAllDocuments();
        for (const doc of allDocs) {
            const v = doc.querySelector('video');
            if (v) return v;
        }
        return null;
    }

    // Global Keydown Handler
    function handleKeydown(e) {
        const tag = (e.target.tagName || '').toLowerCase();
        if (tag === 'input' || tag === 'textarea' || e.target.isContentEditable) {
            return;
        }

        const video = getTargetVideo();
        if (!video) return;

        const doc = video.ownerDocument;
        const wrapper = video.closest('.lms-player-wrapper') || video.parentElement;

        switch (e.key) {
            // Play / Pause
            case ' ':
            case 'k':
            case 'K':
                e.preventDefault();
                e.stopPropagation();
                e.stopImmediatePropagation();
                if (video.paused) {
                    video.play().catch(() => {});
                    showHUD(video, '▶ Play');
                } else {
                    video.pause();
                    showHUD(video, '❚❚ Pause');
                }
                break;

            // Seek -10s / +10s
            case 'j':
            case 'J':
                e.preventDefault();
                e.stopPropagation();
                video.currentTime = Math.max(0, video.currentTime - 10);
                showHUD(video, '⏪ -10s');
                break;
            case 'l':
            case 'L':
                e.preventDefault();
                e.stopPropagation();
                video.currentTime = Math.min(video.duration || Infinity, video.currentTime + 10);
                showHUD(video, '⏩ +10s');
                break;

            // Fine Seek -5s / +5s
            case 'ArrowLeft':
                e.preventDefault();
                e.stopPropagation();
                video.currentTime = Math.max(0, video.currentTime - 5);
                showHUD(video, '⏪ -5s');
                break;
            case 'ArrowRight':
                e.preventDefault();
                e.stopPropagation();
                video.currentTime = Math.min(video.duration || Infinity, video.currentTime + 5);
                showHUD(video, '⏩ +5s');
                break;

            // Volume Up / Down
            case 'ArrowUp':
                e.preventDefault();
                e.stopPropagation();
                video.volume = Math.min(1, Math.round((video.volume + 0.05) * 100) / 100);
                showHUD(video, `🔊 Vol: ${Math.round(video.volume * 100)}%`);
                break;
            case 'ArrowDown':
                e.preventDefault();
                e.stopPropagation();
                video.volume = Math.max(0, Math.round((video.volume - 0.05) * 100) / 100);
                showHUD(video, `🔉 Vol: ${Math.round(video.volume * 100)}%`);
                break;

            // Mute
            case 'm':
            case 'M':
                e.preventDefault();
                e.stopPropagation();
                video.muted = !video.muted;
                showHUD(video, video.muted ? '🔇 Muted' : `🔊 Vol: ${Math.round(video.volume * 100)}%`);
                break;

            // Speed Decrease (<, ,, [) / Increase (>, ., ])
            case '<':
            case ',':
            case '[':
                if (e.key === '[' || e.shiftKey || e.key === '<') {
                    e.preventDefault();
                    e.stopPropagation();
                    let curIdx = SPEEDS.findIndex(s => s >= video.playbackRate);
                    if (curIdx > 0) {
                        video.playbackRate = SPEEDS[curIdx - 1];
                        showHUD(video, `⚡ Speed: ${video.playbackRate}x`);
                    }
                }
                break;
            case '>':
            case '.':
            case ']':
                if (e.key === ']' || e.shiftKey || e.key === '>') {
                    e.preventDefault();
                    e.stopPropagation();
                    let curIdx = SPEEDS.findIndex(s => s >= video.playbackRate);
                    if (curIdx !== -1 && curIdx < SPEEDS.length - 1) {
                        video.playbackRate = SPEEDS[curIdx + 1];
                        showHUD(video, `⚡ Speed: ${video.playbackRate}x`);
                    }
                }
                break;

            // Fullscreen
            case 'f':
            case 'F':
                e.preventDefault();
                e.stopPropagation();
                const fsTarget = video.closest('.h5p-interactive-video, .h5p-content') || wrapper || video;
                if (!doc.fullscreenElement && !document.fullscreenElement) {
                    if (fsTarget.requestFullscreen) {
                        fsTarget.requestFullscreen().catch(() => video.requestFullscreen().catch(() => {}));
                    } else if (video.requestFullscreen) {
                        video.requestFullscreen().catch(() => {});
                    }
                } else {
                    if (doc.exitFullscreen) doc.exitFullscreen().catch(() => {});
                    else if (document.exitFullscreen) document.exitFullscreen().catch(() => {});
                }
                break;

            // Toggle CC
            case 'c':
            case 'C':
                e.preventDefault();
                e.stopPropagation();
                if (video._toggleCC) video._toggleCC();
                break;

            // CC Font Size (+ and -)
            case '+':
            case '=':
                if (video._changeCCFontSize) {
                    e.preventDefault();
                    e.stopPropagation();
                    video._changeCCFontSize(2);
                }
                break;
            case '-':
            case '_':
                if (video._changeCCFontSize) {
                    e.preventDefault();
                    e.stopPropagation();
                    video._changeCCFontSize(-2);
                }
                break;

            // Jump to Percentage (0 to 9)
            default:
                if (e.key >= '0' && e.key <= '9' && !e.ctrlKey && !e.altKey && !e.metaKey) {
                    if (video.duration && isFinite(video.duration)) {
                        e.preventDefault();
                        e.stopPropagation();
                        const pct = parseInt(e.key) * 10;
                        video.currentTime = (video.duration * pct) / 100;
                        showHUD(video, `⏱ ${pct}%`);
                    }
                }
                break;
        }
    }

    // Attach Keydown & Observers to all windows/documents
    function scanAndHookAll() {
        const allDocs = getAllDocuments();
        for (const doc of allDocs) {
            ensureStyles(doc);

            const win = doc.defaultView;
            if (win && !win.__lmsKeyHooked) {
                win.__lmsKeyHooked = true;
                win.addEventListener('keydown', handleKeydown, true);
                console.log('[LMS Enhancer 2.0] Attached keydown listener to window of:', doc.title || doc.location.href);
            }

            // Find videos
            doc.querySelectorAll('video').forEach(setupVideo);

            // Unlock H5P restrictions in this document
            if (win && win.H5P && Array.isArray(win.H5P.instances)) {
                win.H5P.instances.forEach(inst => {
                    if (inst.options && inst.options.preventSkipping) {
                        inst.options.preventSkipping = false;
                    }
                    if (inst.preventSkipping) {
                        inst.preventSkipping = false;
                    }
                    if (inst.controls) {
                        if (typeof inst.controls.enableSeeking === 'function') inst.controls.enableSeeking();
                        if (typeof inst.controls.enableSeek === 'function') inst.controls.enableSeek();
                    }
                    if ('maxTime' in inst) inst.maxTime = Infinity;
                    if (inst.video && 'maxTime' in inst.video) inst.video.maxTime = Infinity;
                });
            }

            doc.querySelectorAll('.h5p-seek-bar, .h5p-slider, .h5p-controls, .h5p-disable-seeking, .h5p-seekbar').forEach(el => {
                el.classList.remove('h5p-disable-seeking');
                el.style.pointerEvents = 'auto';
                el.style.opacity = '1';
            });

            // Attach MutationObserver if not already attached
            if (doc.body && !doc.__lmsObserverHooked) {
                doc.__lmsObserverHooked = true;
                const obs = new MutationObserver(() => {
                    doc.querySelectorAll('video').forEach(setupVideo);
                });
                obs.observe(doc.body, { childList: true, subtree: true });
            }
        }
    }

    // Run immediately and poll periodically to catch async loaded iframes
    scanAndHookAll();
    const intervalId = setInterval(scanAndHookAll, 1000);

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', scanAndHookAll);
    }
    window.addEventListener('load', scanAndHookAll);
})();
