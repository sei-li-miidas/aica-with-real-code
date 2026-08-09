import { MouseEventHandler } from "react";

/**
 * Hook to provide app-related actions
 */
export const useAppActions = () => {
  /**
   * Shows a dialog for external links
   */
  const showExternalLinkDialog: MouseEventHandler<HTMLAnchorElement> = (
    event,
  ) => {
    // Implementation would depend on how you want to handle external links without Redux
    // This could use React Context, a modal library, or other state management approach
    const href = event.currentTarget.getAttribute("href");
    if (href) {
      // Example implementation - could be replaced with your preferred approach
      if (
        window.confirm(
          `This link will take you to an external site: ${href}. Continue?`,
        )
      ) {
        window.open(href, "_blank", "noopener,noreferrer");
      }
    }
    event.preventDefault();
  };

  return {
    showExternalLinkDialog,
  };
};
