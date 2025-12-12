"use client";

import { useState, useCallback } from "react";
import { useDropzone } from "react-dropzone";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Upload, X, FileVideo, Film, CheckCircle, Link as LinkIcon, ChevronDown, ChevronUp } from "lucide-react";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";

import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from "@/components/ui/dialog";
import { Settings, Wand2 } from "lucide-react";

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export default function UploadPage() {
    const [file, setFile] = useState<File | null>(null);
    const [uploading, setUploading] = useState(false);
    const [processing, setProcessing] = useState(false);
    const [progress, setProgress] = useState(0);
    const [clips, setClips] = useState<any[]>([]);
    const [numShorts, setNumShorts] = useState<number>(4);
    const [captionStyle, setCaptionStyle] = useState<string>("Karaoke");
    const [language, setLanguage] = useState<string>("");
    const [clipDuration, setClipDuration] = useState<number>(60);
    const [startTime, setStartTime] = useState<string>("");
    const [endTime, setEndTime] = useState<string>("");

    // Customization State
    const [customizingClip, setCustomizingClip] = useState<any | null>(null);
    const [sharingClip, setSharingClip] = useState<any | null>(null);
    const [sharePlatform, setSharePlatform] = useState<'instagram' | 'youtube' | null>(null);
    const [shareUsername, setShareUsername] = useState("");
    const [sharePassword, setSharePassword] = useState("");
    const [sharingVideo, setSharingVideo] = useState(false);

    const [regenStyle, setRegenStyle] = useState<string>("Karaoke");
    const [regenColor, setRegenColor] = useState<string>("#FFFFFF");
    const [regenBgColor, setRegenBgColor] = useState<string>("#000000"); // Default BG
    const [regenSize, setRegenSize] = useState<number>(18);
    const [isRegenerating, setIsRegenerating] = useState(false);

    // URL & Advanced Settings State
    const [uploadMode, setUploadMode] = useState<'file' | 'url'>('file');
    const [videoUrl, setVideoUrl] = useState<string>("");
    const [showAdvanced, setShowAdvanced] = useState(false);

    // Initial Customization State
    const [customColor, setCustomColor] = useState<string>("#FFFFFF");
    const [customBgColor, setCustomBgColor] = useState<string>(""); // Empty implies default/none
    const [customSize, setCustomSize] = useState<number>(18);

    const captionStyles = [
        { id: "Karaoke", name: "Karaoke", color: "text-green-400", bg: "" },
        { id: "Deep Diver", name: "Deep Diver", color: "text-white", bg: "bg-zinc-800 border-2" },
        { id: "Mozi", name: "Mozi", color: "text-purple-400", bg: "", border: "border-yellow-400 border" },
        { id: "Glitch", name: "Glitch", color: "text-red-500", bg: "", shadow: "shadow-red-500/50" },
        { id: "Classic", name: "Classic", color: "text-white", bg: "" }
    ];

    const onDrop = useCallback((acceptedFiles: File[]) => {
        if (acceptedFiles?.length > 0) {
            setFile(acceptedFiles[0]);
            setProgress(0);
            setClips([]); // Reset clips on new upload
        }
    }, []);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: {
            'video/*': ['.mp4', '.mov', '.avi', '.mkv']
        },
        maxFiles: 1,
        multiple: false
    });

    const removeFile = () => {
        setFile(null);
        setProgress(0);
        setClips([]);
    };

    const parseTimeToSeconds = (timeStr: string) => {
        if (!timeStr) return undefined;
        // Simple HH:MM:SS or MM:SS parser or just seconds
        if (timeStr.includes(":")) {
            const parts = timeStr.split(":").map(Number);
            if (parts.length === 3) return parts[0] * 3600 + parts[1] * 60 + parts[2];
            if (parts.length === 2) return parts[0] * 60 + parts[1];
        }
        return parseFloat(timeStr);
    };

    const runValidation = () => {
        // Basic verification
        if (startTime && endTime) {
            const start = parseTimeToSeconds(startTime);
            const end = parseTimeToSeconds(endTime);
            if (start !== undefined && end !== undefined && start >= end) {
                alert("Start time must be less than End time");
                return false;
            }
        }
        return true;
    };

    const handleProcess = (fileId: string | null = null, savedPath: string | null = null) => {
        setUploading(false);
        setProcessing(true);

        const payload: any = {
            num_shorts: numShorts,
            caption_style: captionStyle,
            language: language,
            clip_duration: clipDuration,
            processing_start_time: startTime ? parseTimeToSeconds(startTime) : undefined,
            processing_end_time: endTime ? parseTimeToSeconds(endTime) : undefined,
            // Advanced Customization
            custom_color: customColor !== "#FFFFFF" ? customColor : undefined,
            custom_bg_color: customBgColor || undefined,
            custom_size: customSize !== 18 ? customSize : undefined
        };

        if (uploadMode === 'file') {
            payload.file_id = fileId;
            payload.video_path = savedPath;
        } else {
            payload.video_url = videoUrl;
        }

        fetch(`${API_BASE_URL}/api/process`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(payload)
        })
            .then(res => res.json())
            .then(data => {
                console.log("Processing complete:", data);
                setProcessing(false);
                if (data.clips && data.clips.length > 0) {
                    setClips(data.clips);
                } else {
                    alert("No clips were generated.");
                }
            })
            .catch(err => {
                console.error("Processing error:", err);
                setProcessing(false);
                alert("Processing failed.");
            });
    };

    const handleUpload = async () => {
        setClips([]);

        if (uploadMode === 'url') {
            if (!videoUrl) {
                alert("Please enter a valid URL");
                return;
            }
            if (runValidation()) {
                handleProcess();
            }
            return;
        }

        if (!file) return;

        if (!runValidation()) return;

        setUploading(true);
        setProgress(0);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const xhr = new XMLHttpRequest();
            xhr.open("POST", `${API_BASE_URL}/api/upload`, true);

            xhr.upload.onprogress = (event) => {
                if (event.lengthComputable) {
                    const percentComplete = (event.loaded / event.total) * 100;
                    setProgress(Math.round(percentComplete));
                }
            };

            xhr.onload = () => {
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    console.log("Upload success:", response);
                    handleProcess(response.file_id, response.saved_path);
                } else {
                    console.error("Upload failed");
                    setUploading(false);
                    alert("Upload failed. Please try again.");
                }
            };

            xhr.onerror = () => {
                console.error("Upload error");
                setUploading(false);
                alert("Network error. Verify backend is running.");
            };

            xhr.send(formData);
        } catch (error) {
            console.error("Error uploading:", error);
            setUploading(false);
        }
    };

    // Wrap handleUpload to include validation
    const handleUploadValidated = () => {
        handleUpload();
    };


    const openCustomize = (clip: any) => {
        setCustomizingClip(clip);
        // Default to current global style or 'Karaoke'
        setRegenStyle(captionStyle);
    };

    const openShare = (clip: any, platform: 'instagram' | 'youtube') => {
        setSharingClip(clip);
        setSharePlatform(platform);
    };

    const handleShare = async () => {
        if (!sharingClip || !sharePlatform) return;
        setSharingVideo(true);

        try {
            const endpoint = sharePlatform === 'instagram' ?
                `${API_BASE_URL}/api/share/instagram` :
                `${API_BASE_URL}/api/share/youtube`;

            const payload = {
                video_path: sharingClip.path,
                caption: `${sharingClip.title || ''}\n\n${sharingClip.description || ''}\n\n${(sharingClip.hashtags || []).join(' ')}`,
                username: shareUsername,
                password: sharePassword
            };

            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            const data = await res.json();
            if (!res.ok) throw new Error(data.detail || "Sharing failed");

            alert(`${sharePlatform} Share Successful!`);
            setSharingClip(null);
            setSharePassword(""); // Clear sensitive

        } catch (e: any) {
            console.error(e);
            alert(`Sharing Failed: ${e.message}`);
        } finally {
            setSharingVideo(false);
        }
    };

    const handleRegenerate = async () => {
        if (!customizingClip) return;
        setIsRegenerating(true);

        try {
            // Need the file_id. Assuming clip name format "{file_id}_short_{i}.mp4"
            // But we stored original_file in the process response. 
            // Better to parse from clip filename or if we had it in clip object.
            // Wait, we didn't store file_id in clip object in backend.
            // We can extract it from the URL or Path.
            // URL: /static/file_id_short_1.mp4
            const filename = customizingClip.url.split('/').pop();
            // This is risky parsing. 
            // In process.py we return "original_file": request.file_id in the processing response.
            // But here we only have the clip object.
            // We can find the file_id from the clip path if we assume standard format.
            // Or we can rely on the fact that file_id is typically UUID-like at start.
            // Let's assume standard format: {uuid}_short_{n}.mp4.
            const fileId = filename.split('_short_')[0];

            const payload = {
                file_id: fileId,
                start_time: customizingClip.start,
                end_time: customizingClip.end,
                caption_style: regenStyle,
                custom_color: regenColor,
                custom_bg_color: regenBgColor,
                custom_size: regenSize
            };

            const res = await fetch(`${API_BASE_URL}/api/process/regenerate`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(payload)
            });

            if (!res.ok) throw new Error("Regeneration failed");

            const data = await res.json();

            // Update the clip in the list
            setClips(prevClips => prevClips.map(c => {
                if (c === customizingClip) {
                    return { ...c, url: data.url, path: data.path }; // Update URL to new regen file
                }
                return c;
            }));

            setCustomizingClip(null); // Close dialog

        } catch (e) {
            console.error(e);
            alert("Regeneration failed. See console.");
        } finally {
            setIsRegenerating(false);
        }
    };

    return (
        <div className="min-h-screen bg-background text-foreground flex flex-col items-center py-20 px-6">
            <div className="max-w-4xl w-full">
                <div className="mb-10 text-center">
                    <h1 className="text-4xl font-bold mb-2 tracking-tight">Upload Your Video</h1>
                    <p className="text-muted-foreground">Supports MP4, MOV, MKV up to 2GB.</p>
                </div>

                <Card className="border-border/50 bg-card/50 backdrop-blur-sm mb-12">
                    <CardContent className="pt-6">
                        <Tabs defaultValue="file" className="w-full mb-6" onValueChange={(v) => setUploadMode(v as 'file' | 'url')}>
                            <TabsList className="grid w-full grid-cols-2">
                                <TabsTrigger value="file">File Upload</TabsTrigger>
                                <TabsTrigger value="url">YouTube URL</TabsTrigger>
                            </TabsList>

                            <TabsContent value="file" className="mt-4">
                                {!file ? (
                                    <div
                                        {...getRootProps()}
                                        className={`border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all duration-300 ${isDragActive ? 'border-primary bg-primary/5' : 'border-border/50 hover:border-primary/50 hover:bg-secondary/50'}`}
                                    >
                                        <input {...getInputProps()} />
                                        <div className="flex flex-col items-center gap-4">
                                            <div className="p-4 bg-background rounded-full border border-border/50 shadow-sm">
                                                <Upload className="h-8 w-8 text-primary" />
                                            </div>
                                            <div>
                                                <p className="font-semibold text-lg mb-1">Click to upload or drag and drop</p>
                                                <p className="text-sm text-muted-foreground">Video (MP4, MOV)</p>
                                            </div>
                                        </div>
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-4 p-4 border border-border/50 rounded-lg bg-secondary/20 animate-in fade-in slide-in-from-bottom-2">
                                        <div className="bg-primary/20 p-3 rounded-lg">
                                            <FileVideo className="h-6 w-6 text-primary" />
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="font-medium truncate">{file.name}</p>
                                            <p className="text-xs text-muted-foreground">{(file.size / (1024 * 1024)).toFixed(2)} MB</p>
                                        </div>
                                        {!uploading && (
                                            <Button variant="ghost" size="icon" onClick={removeFile} className="hover:text-destructive">
                                                <X className="h-4 w-4" />
                                            </Button>
                                        )}
                                    </div>
                                )}
                            </TabsContent>

                            <TabsContent value="url" className="mt-4">
                                <div className="space-y-4">
                                    <div className="flex gap-2">
                                        <div className="relative flex-1">
                                            <LinkIcon className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                                            <Input
                                                placeholder="Paste YouTube URL here..."
                                                className="pl-9"
                                                value={videoUrl}
                                                onChange={(e) => setVideoUrl(e.target.value)}
                                            />
                                        </div>
                                    </div>
                                    <p className="text-xs text-muted-foreground">Supports YouTube videos and Shorts.</p>
                                </div>
                            </TabsContent>
                        </Tabs>

                        {/* Settings Section (Visible if File Selected OR URL Entered) */}
                        {((uploadMode === 'file' && file) || (uploadMode === 'url' && videoUrl)) && (
                            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 mt-6 border-t border-border/50 pt-6">

                                {!uploading && !processing && progress === 0 && (
                                    <>
                                        <div className="flex flex-col gap-2">
                                            <label htmlFor="numShorts" className="text-sm font-medium text-muted-foreground">Number of Shorts to Generate:</label>
                                            <Input
                                                id="numShorts"
                                                type="number"
                                                min={1}
                                                max={10}
                                                value={numShorts}
                                                onChange={(e) => setNumShorts(parseInt(e.target.value) || 1)}
                                                className="w-full max-w-[200px]"
                                            />
                                        </div>

                                        <div className="flex flex-col gap-2">
                                            <label htmlFor="language" className="text-sm font-medium text-muted-foreground">Language:</label>
                                            <select
                                                id="language"
                                                value={language}
                                                onChange={(e) => setLanguage(e.target.value)}
                                                className="w-full max-w-[200px] flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                            >
                                                <option value="en">English</option>
                                                <option value="te">Telugu</option>
                                                <option value="">Auto Detect</option>
                                            </select>
                                        </div>

                                        <div className="flex flex-col gap-2">
                                            <label htmlFor="clipDuration" className="text-sm font-medium text-muted-foreground">Clip Duration:</label>
                                            <select
                                                id="clipDuration"
                                                value={clipDuration}
                                                onChange={(e) => setClipDuration(Number(e.target.value))}
                                                className="w-full max-w-[200px] flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                                            >
                                                <option value={30}>30 Seconds</option>
                                                <option value={60}>60 Seconds</option>
                                                <option value={90}>90 Seconds</option>
                                                <option value={120}>120 Seconds</option>
                                            </select>
                                        </div>

                                        <div className="grid grid-cols-2 gap-4 max-w-[400px]">
                                            <div className="flex flex-col gap-2">
                                                <label htmlFor="startTime" className="text-sm font-medium text-muted-foreground">Start Time (HH:MM:SS):</label>
                                                <Input
                                                    id="startTime"
                                                    type="text"
                                                    placeholder="00:00:00"
                                                    value={startTime}
                                                    onChange={(e) => setStartTime(e.target.value)}
                                                />
                                            </div>
                                            <div className="flex flex-col gap-2">
                                                <label htmlFor="endTime" className="text-sm font-medium text-muted-foreground">End Time (HH:MM:SS):</label>
                                                <Input
                                                    id="endTime"
                                                    type="text"
                                                    placeholder="00:00:00"
                                                    value={endTime}
                                                    onChange={(e) => setEndTime(e.target.value)}
                                                />
                                            </div>
                                        </div>

                                        <div className="space-y-3">
                                            <label className="text-sm font-medium text-muted-foreground">Caption Style:</label>
                                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-5 gap-3">
                                                {captionStyles.map((style) => (
                                                    <div
                                                        key={style.id}
                                                        onClick={() => setCaptionStyle(style.id)}
                                                        className={`cursor-pointer rounded-lg p-3 text-center transition-all ${captionStyle === style.id
                                                            ? 'ring-2 ring-primary scale-105'
                                                            : 'hover:bg-secondary/50'
                                                            } bg-secondary/20 border border-border/50`}
                                                    >
                                                        <div className={`h-12 w-full mb-2 rounded flex items-center justify-center font-bold text-sm ${style.bg} ${style.color} ${style.border || ''} ${style.shadow || ''}`}>
                                                            ABC
                                                        </div>
                                                        <p className="text-xs font-medium">{style.name}</p>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Advanced Settings Checkbox/Collapse */}
                                        <div className="border rounded-lg p-4 bg-secondary/10">
                                            <button
                                                onClick={() => setShowAdvanced(!showAdvanced)}
                                                className="flex items-center justify-between w-full text-sm font-medium text-muted-foreground hover:text-foreground transition-colors"
                                            >
                                                <span className="flex items-center gap-2"><Settings className="h-4 w-4" /> Advanced Customization</span>
                                                {showAdvanced ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
                                            </button>

                                            {showAdvanced && (
                                                <div className="mt-4 grid grid-cols-1 sm:grid-cols-3 gap-4 animate-in fade-in slide-in-from-top-2">
                                                    <div className="space-y-2">
                                                        <label className="text-xs font-medium">Text Color</label>
                                                        <div className="flex gap-2">
                                                            <Input
                                                                type="color"
                                                                value={customColor}
                                                                onChange={(e) => setCustomColor(e.target.value)}
                                                                className="w-10 h-9 p-1 cursor-pointer"
                                                            />
                                                            <Input
                                                                type="text"
                                                                value={customColor}
                                                                onChange={(e) => setCustomColor(e.target.value)}
                                                                className="flex-1 h-9 text-xs"
                                                            />
                                                        </div>
                                                    </div>

                                                    <div className="space-y-2">
                                                        <label className="text-xs font-medium">Background Color</label>
                                                        <div className="flex gap-2">
                                                            <Input
                                                                type="color"
                                                                value={customBgColor || "#000000"}
                                                                onChange={(e) => setCustomBgColor(e.target.value)}
                                                                className="w-10 h-9 p-1 cursor-pointer"
                                                            />
                                                            <Input
                                                                type="text"
                                                                placeholder="None"
                                                                value={customBgColor}
                                                                onChange={(e) => setCustomBgColor(e.target.value)}
                                                                className="flex-1 h-9 text-xs"
                                                            />
                                                        </div>
                                                    </div>

                                                    <div className="space-y-2">
                                                        <label className="text-xs font-medium">Font Size</label>
                                                        <Input
                                                            type="number"
                                                            value={customSize}
                                                            onChange={(e) => setCustomSize(parseInt(e.target.value))}
                                                            className="h-9"
                                                        />
                                                    </div>
                                                </div>
                                            )}
                                        </div>
                                    </>
                                )}

                                {uploading && (
                                    <div className="space-y-2">
                                        <div className="flex justify-between text-sm">
                                            <span>Uploading...</span>
                                            <span>{progress}%</span>
                                        </div>
                                        <Progress value={progress} className="h-2" />
                                    </div>
                                )}

                                {!uploading && !processing && progress === 100 && (
                                    <div className="flex items-center justify-center gap-2 text-green-500 font-medium py-2">
                                        <CheckCircle className="h-5 w-5" /> Processing Complete
                                    </div>
                                )}

                                {processing && (
                                    <div className="space-y-2 mt-4">
                                        <div className="flex items-center justify-center gap-2 text-primary font-medium">
                                            <Film className="h-5 w-5 animate-spin" />
                                            <span>Transcribing and Analyzing Video...</span>
                                        </div>
                                        <p className="text-xs text-center text-muted-foreground">This may take a minute.</p>
                                    </div>
                                )}

                                <div className="flex justify-end pt-2">
                                    <Button
                                        onClick={handleUploadValidated}
                                        disabled={uploading || processing || (progress === 100 && !processing)}
                                        size="lg"
                                        className="w-full sm:w-auto relative overflow-hidden"
                                    >
                                        {uploading ? (
                                            <span className="flex items-center gap-2">Uploading... <Film className="h-4 w-4 animate-spin" /></span>
                                        ) : processing ? (
                                            "Processing..."
                                        ) : progress === 100 ? (
                                            "Done"
                                        ) : (
                                            "Start Processing"
                                        )}
                                    </Button>
                                </div>
                            </div>
                        )}
                    </CardContent>
                </Card>

                {clips.length > 0 && (
                    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-700">
                        <div className="flex items-center gap-2 mb-6">
                            <Film className="h-6 w-6 text-primary" />
                            <h2 className="text-2xl font-bold">Generated Shorts</h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                            {clips.map((clip, index) => (
                                <Card key={index} className="overflow-hidden border-border/50 bg-card/50 backdrop-blur-sm hover:border-primary/50 transition-colors">
                                    <div className="aspect-[9/16] bg-black relative">
                                        <video
                                            src={`${API_BASE_URL}${clip.url}`}
                                            controls
                                            className="w-full h-full object-contain"
                                        />
                                    </div>
                                    <CardContent className="p-4 space-y-3">
                                        <div>
                                            <Badge variant="secondary" className="mb-2">Clip {index + 1}</Badge>
                                            <p className="text-sm text-muted-foreground line-clamp-2" title={clip.reason}>
                                                {clip.reason}
                                            </p>
                                        </div>
                                        <div className="flex gap-2">
                                            <Button asChild className="flex-1" variant="outline">
                                                <a href={`${API_BASE_URL}${clip.url}`} download target="_blank" rel="noreferrer">
                                                    Download
                                                </a>
                                            </Button>
                                            <Button
                                                variant="secondary"
                                                className="flex-1 gap-2"
                                                onClick={() => openCustomize(clip)}
                                            >
                                                <Settings className="w-4 h-4" /> Customize
                                            </Button>
                                        </div>
                                        <div className="flex gap-2 pt-2 border-t border-border/20">
                                            <Button
                                                variant="ghost"
                                                className="w-full text-xs h-8 hover:bg-pink-500/10 hover:text-pink-500"
                                                onClick={() => openShare(clip, 'instagram')}
                                            >
                                                Share to Instagram
                                            </Button>
                                        </div>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                )}
            </div>

            <Dialog open={!!customizingClip} onOpenChange={(open) => !open && setCustomizingClip(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Customize Captions (AI)</DialogTitle>
                        <DialogDescription>
                            Regenerate this clip with different caption styles using the original AI transcript.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Style</label>
                            <select
                                value={regenStyle}
                                onChange={(e) => setRegenStyle(e.target.value)}
                                className="w-full flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                {captionStyles.map(s => (
                                    <option key={s.id} value={s.id}>{s.name}</option>
                                ))}
                            </select>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="space-y-2">
                                <label className="text-sm font-medium">Text Color</label>
                                <div className="flex gap-2">
                                    <Input
                                        type="color"
                                        value={regenColor}
                                        onChange={(e) => setRegenColor(e.target.value)}
                                        className="w-12 h-10 p-1 cursor-pointer"
                                    />
                                    <Input
                                        type="text"
                                        value={regenColor}
                                        onChange={(e) => setRegenColor(e.target.value)}
                                        className="flex-1"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Background Color</label>
                                <div className="flex gap-2">
                                    <Input
                                        type="color"
                                        value={regenBgColor}
                                        onChange={(e) => setRegenBgColor(e.target.value)}
                                        className="w-12 h-10 p-1 cursor-pointer"
                                    />
                                    <Input
                                        type="text"
                                        value={regenBgColor}
                                        onChange={(e) => setRegenBgColor(e.target.value)}
                                        className="flex-1"
                                    />
                                </div>
                            </div>

                            <div className="space-y-2">
                                <label className="text-sm font-medium">Font Size</label>
                                <Input
                                    type="number"
                                    value={regenSize}
                                    onChange={(e) => setRegenSize(parseInt(e.target.value))}
                                />
                            </div>
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setCustomizingClip(null)} disabled={isRegenerating}>
                            Cancel
                        </Button>
                        <Button onClick={handleRegenerate} disabled={isRegenerating}>
                            {isRegenerating ? (
                                <>
                                    <Wand2 className="mr-2 h-4 w-4 animate-spin" /> Regenerating...
                                </>
                            ) : (
                                <>
                                    <Wand2 className="mr-2 h-4 w-4" /> Regenerate Video
                                </>
                            )}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>
            <Dialog open={!!sharingClip} onOpenChange={(open) => !open && setSharingClip(null)}>
                <DialogContent>
                    <DialogHeader>
                        <DialogTitle>Share to {sharePlatform === 'instagram' ? "Instagram" : "YouTube"}</DialogTitle>
                        <DialogDescription>
                            Post this clip directly to your social media account.
                        </DialogDescription>
                    </DialogHeader>

                    <div className="space-y-4 py-4">
                        <div className="p-3 bg-secondary/20 rounded-md text-sm">
                            <p className="font-semibold">{sharingClip?.title}</p>
                            <p className="text-muted-foreground mt-1 text-xs line-clamp-3">{sharingClip?.description}</p>
                            <p className="text-blue-400 mt-2 text-xs">{(sharingClip?.hashtags || []).join(' ')}</p>
                        </div>

                        <div className="space-y-2">
                            <label className="text-sm font-medium">Username</label>
                            <Input value={shareUsername} onChange={(e) => setShareUsername(e.target.value)} placeholder="Instagram Username" />
                        </div>
                        <div className="space-y-2">
                            <label className="text-sm font-medium">Password</label>
                            <Input type="password" value={sharePassword} onChange={(e) => setSharePassword(e.target.value)} placeholder="Instagram Password" />
                        </div>
                    </div>

                    <DialogFooter>
                        <Button variant="outline" onClick={() => setSharingClip(null)} disabled={sharingVideo}>Cancel</Button>
                        <Button onClick={handleShare} disabled={sharingVideo} className="bg-gradient-to-r from-purple-500 to-pink-500 hover:from-purple-600 hover:to-pink-600 text-white border-0">
                            {sharingVideo ? "Sharing..." : "Post Now"}
                        </Button>
                    </DialogFooter>
                </DialogContent>
            </Dialog>

        </div>
    );
}
