"use client";

import { Button } from "@heroui/react";

/** Trạng thái trang thống nhất: đang tải / rỗng. Trả null khi có dữ liệu. */
export function PageState({
	loading,
	empty,
	emptyText = "Chưa có dữ liệu.",
}: {
	loading: boolean;
	empty: boolean;
	emptyText?: string;
}) {
	if (loading)
		return (
			<div
				className="flex items-center gap-2 py-8 justify-center text-sm text-neutral-500"
				data-testid="loading"
			>
				<span className="inline-block w-4 h-4 rounded-full border-2 border-neutral-300 border-t-primary animate-spin" />
				Đang tải…
			</div>
		);
	if (empty)
		return (
			<p
				className="py-8 text-center text-sm text-neutral-500"
				data-testid="empty"
			>
				{emptyText}
			</p>
		);
	return null;
}

/** Nút phân trang Trước/Sau đơn giản (không cần tổng số bản ghi). */
export function Pager({
	page,
	setPage,
	hasMore,
}: {
	page: number;
	setPage: (p: number) => void;
	hasMore: boolean;
}) {
	if (page === 0 && !hasMore) return null;
	return (
		<div className="flex items-center gap-2 mt-3">
			<Button
				variant="ghost"
				isDisabled={page === 0}
				onPress={() => setPage(page - 1)}
				data-testid="pager-prev"
			>
				← Trước
			</Button>
			<span className="text-sm text-neutral-500" data-testid="pager-page">
				Trang {page + 1}
			</span>
			<Button
				variant="ghost"
				isDisabled={!hasMore}
				onPress={() => setPage(page + 1)}
				data-testid="pager-next"
			>
				Sau →
			</Button>
		</div>
	);
}
