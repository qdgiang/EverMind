export function ApiError({ message }: { message: string }) {
  return (
    <p role="alert" className="rounded-md border border-red-300 bg-red-50 p-3 text-sm text-red-800">
      Could not load this view: {message}
    </p>
  );
}
