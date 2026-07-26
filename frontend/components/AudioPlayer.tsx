"use client";

import { useEffect, useState } from "react";

import { mediaBlobUrl } from "@/lib/api";

/** Phát audio bảo vệ bằng token: tải blob qua API rồi gắn vào <audio>. */
export function AudioPlayer({ mediaKey }: { mediaKey: string }) {
	const [url, setUrl] = useState("");
	const [err, setErr] = useState(false);

	useEffect(() => {
		let objectUrl = "";
		mediaBlobUrl(mediaKey)
			.then((u) => {
				objectUrl = u;
				setUrl(u);
			})
			.catch(() => setErr(true));
		return () => {
			if (objectUrl) URL.revokeObjectURL(objectUrl);
		};
	}, [mediaKey]);

	if (err) return <p className="text-danger text-sm">Không tải được audio.</p>;
	if (!url) return <p className="text-sm text-neutral-500">Đang tải audio…</p>;
	return (
		// biome-ignore lint/a11y/useMediaCaption: audio đề thi nghe — không có phụ đề
		<audio controls src={url} className="w-full" data-testid="audio-player" />
	);
}
