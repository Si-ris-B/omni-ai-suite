import React, { useState, useEffect, useCallback, useRef } from 'react';
import { getServiceStatus, startService, stopService } from '../../services/api'; // Import API functions
import {
  Box,
  Button,
  Text,
  Spinner,
  Badge,
  HStack,
  useToast,
  VStack,
  Heading,
  useInterval, // Chakra hook for intervals
  Alert,
  AlertIcon,
  AlertTitle,
  AlertDescription,
  CloseButton,
} from '@chakra-ui/react';

function ServiceControl({ serviceName = 'stt', title = 'STT Service Control' }) {
  const [status, setStatus] = useState('loading'); // 'loading', 'running', 'exited', 'created', 'error', 'unknown', 'not_found'
  const [isActionLoading, setIsActionLoading] = useState(false); // Loading state specifically for button actions
  const [lastError, setLastError] = useState(null); // Store last error message
  const toast = useToast();
  const isMounted = useRef(true); // Ref to track component mount status
  const toastIdRef = useRef(); // Ref to manage toast IDs

  // Function to safely close existing toast
  const closeToast = () => {
    if (toastIdRef.current) {
      toast.close(toastIdRef.current);
    }
  }

  // Function to show toast notifications
  const showToast = (id, title, description, status) => {
    closeToast(); // Close previous toast before showing new one
    toastIdRef.current = toast({
      id: id, // Use id to prevent duplicates if needed rapidly
      title: title,
      description: description,
      status: status, // 'success', 'error', 'warning', 'info'
      duration: status === 'error' ? 8000 : 4000, // Longer duration for errors
      isClosable: true,
      position: 'top-right', // Or other position
    });
  }

  // Callback to fetch status safely
  const fetchStatus = useCallback(async (isInitial = false) => {
    if (isActionLoading || !isMounted.current) return;

    if (!isInitial) {
      // console.log(`Polling status for ${serviceName}...`); // Debug log
    } else {
      console.log(`Initial status fetch for ${serviceName}...`);
    }

    try {
      const response = await getServiceStatus(serviceName);
      if (isMounted.current) {
        const newStatus = response.data.status || 'unknown';
        if (newStatus !== status) { // Only update state if status changed
          console.log(`Status changed for ${serviceName}: ${status} -> ${newStatus}`);
          setStatus(newStatus);
          setLastError(null); // Clear error on successful status update
        }
      }
    } catch (error) {
      console.error('Error fetching status:', error.response || error.message);
      const errorMsg = error.response?.data?.error || error.message;
      if (isMounted.current) {
        setStatus('error');
        setLastError(errorMsg); // Store the error message
        // Only show toast on initial fetch failure or if status wasn't already error
        if (isInitial || status !== 'error') {
          showToast(`status-error-${serviceName}`, 'Error Fetching Status', errorMsg, 'error');
        }
      }
    }
  }, [serviceName, isActionLoading, toast, status]); // Include status

  // Fetch status on initial mount
  useEffect(() => {
    isMounted.current = true;
    fetchStatus(true); // Pass true for initial fetch

    // Cleanup function
    return () => {
      isMounted.current = false;
      closeToast(); // Close any active toast on unmount
    };
  }, []); // Empty dependency array ensures this runs only once on mount

  // Use Chakra's interval hook for polling (only if component is mounted)
  useInterval(() => {
    if (isMounted.current) {
      fetchStatus(false); // Pass false for poll fetches
    }
  }, status === 'loading' || isActionLoading ? null : 5000); // Poll every 5s unless action/loading


  // Handler for start/stop actions
  const handleControl = async (action) => {
    if (!isMounted.current) return;

    setIsActionLoading(true);
    setStatus('loading'); // Indicate action in progress
    setLastError(null); // Clear previous errors
    closeToast(); // Close any lingering status toasts

    const actionVerb = action === 'start' ? 'Starting' : 'Stopping';
    const actionFunc = action === 'start' ? startService : stopService;
    const toastId = `action-${action}-${serviceName}-${Date.now()}`; // Unique ID

    try {
      const response = await actionFunc(serviceName);
      if (isMounted.current) {
        const finalStatus = response.data.status || 'unknown';
        setStatus(finalStatus); // Update status based on response
        showToast(toastId, `Service ${action} requested`, response.data.message || `${actionVerb} request sent. Final status: ${finalStatus}`, 'success');
      }
    } catch (error) {
      console.error(`Error ${action}ing service:`, error.response || error.message);
      const errorMsg = error.response?.data?.error || error.message;
      if (isMounted.current) {
        setStatus('error'); // Set status to error on failure
        setLastError(errorMsg);
        showToast(toastId, `Failed to ${action} service`, errorMsg, 'error');
        // Fetch status again after error to be sure
        fetchStatus(false);
      }
    } finally {
      if (isMounted.current) {
        // Delay slightly before re-enabling buttons
        setTimeout(() => setIsActionLoading(false), 1000);
      }
    }
  };

  // Helper to determine badge color
  const getStatusColorScheme = () => {
    // ... (Switch statement as in previous example: running=green, exited/created=gray, error/not_found=red, loading=yellow, default=blue)
    switch (status) {
      case 'running': return 'green';
      case 'exited':
      case 'created': return 'gray';
      case 'error':
      case 'not_found': return 'red';
      case 'loading': return 'yellow';
      default: return 'blue'; // unknown etc.
    }
  };

  // Determine button disabled states
  const isStartDisabled = isActionLoading || ['running', 'loading', 'error', 'not_found'].includes(status);
  const isStopDisabled = isActionLoading || !['running'].includes(status);

  return (
      <Box p={5} borderWidth="1px" borderRadius="lg" shadow="md" bg="white">
        <VStack spacing={4} align="stretch">
          <HStack justify="space-between">
            <Heading size="md">{title}</Heading>
            <Badge fontSize="0.9em" px={3} py={1} borderRadius="full" variant='solid' colorScheme={getStatusColorScheme()}>
              {isActionLoading ? 'Processing...' : status}
            </Badge>
          </HStack>

          {lastError && status === 'error' && (
              <Alert status='error' variant='subtle' flexDirection='column' alignItems='center' justifyContent='center' textAlign='center' borderRadius="md">
                <AlertIcon boxSize='30px' mr={0}/>
                <AlertTitle mt={2} mb={1} fontSize='lg'>
                  Action/Status Error!
                </AlertTitle>
                <AlertDescription maxWidth='sm'>
                  {lastError}
                </AlertDescription>
                <CloseButton alignSelf='flex-start' position='relative' right={-1} top={-1} onClick={() => setLastError(null)} />
              </Alert>
          )}

          <HStack mt={2} justify="space-around">
            <Button
                leftIcon={isActionLoading && status === 'loading' ? <Spinner size="sm" /> : undefined}
                colorScheme="green"
                variant="solid"
                onClick={() => handleControl('start')}
                isLoading={isActionLoading} // Let Chakra handle spinner via isLoading
                isDisabled={isStartDisabled}
                minW="120px"
            >
              Start Service
            </Button>
            <Button
                leftIcon={isActionLoading && status === 'loading' ? <Spinner size="sm" /> : undefined}
                colorScheme="red"
                variant="solid"
                onClick={() => handleControl('stop')}
                isLoading={isActionLoading}
                isDisabled={isStopDisabled}
                minW="120px"
            >
              Stop Service
            </Button>
          </HStack>
        </VStack>
      </Box>
  );
}

export default ServiceControl;