// File: frontend/src/features/control/ServiceControl.jsx
import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getServiceStatus, startService, stopService } from '../../services/api'; // Assuming api service is correctly set up
import {
  Box,
  Button,
  Spinner,
  Badge,
  HStack,
  VStack,
  Heading,
  Alert,         // Import Alert namespace
  CloseButton,
  Text           // Import Text for Alert Description if needed, or use Alert.Description
} from '@chakra-ui/react';
import { toaster } from "@/components/ui/toaster";

// Custom useInterval hook implementation (remains the same)
const useInterval = (callback, delay) => {
  const savedCallback = useRef();

  useEffect(() => {
    savedCallback.current = callback;
  }, [callback]);

  useEffect(() => {
    function tick() {
      savedCallback.current();
    }
    if (delay !== null) {
      const id = setInterval(tick, delay);
      return () => clearInterval(id);
    }
  }, [delay]);
};

function ServiceControl({ serviceName = 'stt', title = 'STT Service Control' }) {
  const [status, setStatus] = useState('loading');
  const [isActionLoading, setIsActionLoading] = useState(false);
  const [lastError, setLastError] = useState(null);
  const isMounted = useRef(true); // Ref to track mount status

  // Fetch status function using useCallback for stability
  const fetchStatus = useCallback(async (isInitialFetch = false) => {
    // Avoid fetching if an action is already in progress, unless it's the initial fetch
    if (isActionLoading && !isInitialFetch) return;

    if (!isInitialFetch) { // Only set loading state for background polls
      // console.log(`[ServiceControl - ${serviceName}] Polling status...`);
    }

    try {
      const response = await getServiceStatus(serviceName);
      if (!isMounted.current) return; // Check if component is still mounted

      setStatus(response.status);
      if (response.error) {
        // Only show toast if error is new or different
        if (lastError !== response.error) {
          setLastError(response.error);
          // Use toaster API from docs
          toaster.error({
            id: `${serviceName}-status-error`, // Unique ID is good practice
            title: 'Status Update Error',
            description: response.error,
          });
        }
      } else if (lastError) {
        // Clear error if status is now okay
        setLastError(null);
      }
    } catch (error) {
      if (!isMounted.current) return; // Check mount status on error
      const errorMsg = error instanceof Error ? error.message : String(error);
      // Only show toast if error is new or different
      if (lastError !== errorMsg) {
        setStatus('error'); // Set status to error on fetch failure
        setLastError(errorMsg);
        // Use toaster API from docs
        toaster.error({
          id: `${serviceName}-fetch-error`,
          title: 'Status Fetch Failed',
          description: errorMsg,
        });
      }
    } finally {
      // Important: Reset action loading state only if it was set by an action,
      // not just by the initial fetch or polling. We handle this in handleControl.
      if (isInitialFetch) {
        // console.log(`[ServiceControl - ${serviceName}] Initial fetch complete.`);
      }
    }
  }, [serviceName, isActionLoading, lastError]); // Added lastError dependency

  // Effect for initial fetch and cleanup
  useEffect(() => {
    isMounted.current = true;
    console.log(`[ServiceControl - ${serviceName}] Mounting and initial fetch...`);
    fetchStatus(true); // Perform initial fetch

    // Cleanup function
    return () => {
      console.log(`[ServiceControl - ${serviceName}] Unmounting.`);
      isMounted.current = false;
      // toaster.dismiss(); // Optional: dismiss all toasts for this component on unmount
    };
  }, [fetchStatus]); // Run only once on mount, fetchStatus is stable due to useCallback

  // Effect for polling status
  useInterval(() => {
    if (isMounted.current) {
      fetchStatus(false); // Pass false to indicate it's not the initial fetch
    }
  }, status === 'loading' || isActionLoading ? null : 5000); // Poll every 5s unless loading/acting

  // Handle start/stop actions
  const handleControl = async (action) => {
    setIsActionLoading(true); // Set loading state for the action button
    setLastError(null); // Clear previous errors before action
    // toaster.dismiss(); // Optional: dismiss previous toasts

    try {
      const response = action === 'start'
          ? await startService(serviceName)
          : await stopService(serviceName);

      if (!isMounted.current) return; // Check mount status after async operation

      if (response.error) {
        setStatus('error'); // Reflect error state locally
        setLastError(response.error);
        toaster.error({ // Use toaster API
          id: `${serviceName}-action-error`,
          title: `${action.charAt(0).toUpperCase() + action.slice(1)} Failed`,
          description: response.error,
        });
      } else {
        setStatus(response.status); // Update status from response
        // setLastError(null); // Already cleared above
        toaster.success({ // Use toaster API
          id: `${serviceName}-action-success`,
          title: 'Success',
          description: `Service ${action} command sent successfully. Status: ${response.status}`,
        });
        // Optionally trigger an immediate status fetch after action
        // fetchStatus(false);
      }
    } catch (error) {
      if (!isMounted.current) return;
      const errorMsg = error instanceof Error ? error.message : String(error);
      setStatus('error'); // Reflect error state locally
      setLastError(errorMsg);
      toaster.error({ // Use toaster API
        id: `${serviceName}-action-error`,
        title: `${action.charAt(0).toUpperCase() + action.slice(1)} Failed`,
        description: errorMsg,
      });
    } finally {
      // Reset loading state *only if* component is still mounted
      if (isMounted.current) {
        setIsActionLoading(false);
      }
    }
  };

  // Determine badge color based on status
  const getStatusColorScheme = () => {
    switch (status) {
      case 'running': return 'green';
      case 'stopped': return 'gray';
      case 'error': return 'red';
      case 'loading': return 'blue'; // Keep loading state distinct
      default: return 'yellow'; // Use yellow for unknown states
    }
  };

  // Determine button disabled states
  const isStartDisabled = isActionLoading || ['running', 'loading'].includes(status);
  const isStopDisabled = isActionLoading || !['running'].includes(status);

  return (
      <Box p={5} borderWidth="1px" borderRadius="lg" shadow="md" bg="white">
        <VStack spacing={4} align="stretch">
          <HStack justify="space-between" align="center">
            <Heading size="md">{title}</Heading>
            <Badge
                colorScheme={getStatusColorScheme()}
                fontSize="md" // Consider adjusting size if needed, e.g., 'sm'
                px={3}
                py={1}
                borderRadius="full"
                display="inline-flex" // Helps align spinner and text
                alignItems="center"
            >
              {/* Show spinner only when loading status, not during button actions */}
              {status === 'loading' ? <Spinner size="xs" mr={2} /> : null}
              {status}
            </Badge>
          </HStack>

          {/* Display lastError if status is 'error' */}
          {lastError && status === 'error' && (
              // Use Alert V3 Structure from docs
              <Alert.Root status='error' variant='subtle' borderRadius="md" mt={2}>
                <Alert.Indicator />
                <Alert.Content>
                  <Alert.Title fontSize="md" fontWeight="semibold">Service Error!</Alert.Title>
                  <Alert.Description fontSize="sm" mt={1}>
                    {lastError}
                  </Alert.Description>
                </Alert.Content>
                <CloseButton
                    position='absolute' // Position relative to Alert.Root
                    right="8px"
                    top="8px"
                    size="sm"
                    onClick={() => setLastError(null)} // Action to clear the error display
                />
              </Alert.Root>
          )}

          <HStack mt={4} justify="space-around"> {/* Added margin top */}
            <Button
                colorScheme="green"
                onClick={() => handleControl('start')}
                isLoading={isActionLoading && !isStartDisabled} // Show spinner only when this button caused the loading
                loadingText="Starting..."
                isDisabled={isStartDisabled}
                width="120px"
            >
              Start
            </Button>
            <Button
                colorScheme="red"
                onClick={() => handleControl('stop')}
                isLoading={isActionLoading && !isStopDisabled} // Show spinner only when this button caused the loading
                loadingText="Stopping..."
                isDisabled={isStopDisabled}
                width="120px"
            >
              Stop
            </Button>
          </HStack>
        </VStack>
      </Box>
  );
}

export default ServiceControl;