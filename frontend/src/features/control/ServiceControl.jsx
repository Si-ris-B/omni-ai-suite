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
} from '@chakra-ui/react';

function ServiceControl({ serviceName = 'stt', title = 'STT Service Control' }) {
  const [status, setStatus] = useState('loading'); // 'loading', 'running', 'exited', 'created', 'error', 'unknown', 'not_found'
  const [isActionLoading, setIsActionLoading] = useState(false); // Loading state specifically for button actions
  const toast = useToast();
  const isMounted = useRef(true); // Ref to track component mount status

  // Callback to fetch status safely
  const fetchStatus = useCallback(async () => {
    // Prevent fetching if an action is in progress or component unmounted
    if (isActionLoading || !isMounted.current) return;

    // console.log(); // Debug log
    try {
      const response = await getServiceStatus(serviceName);
      if (isMounted.current) { // Check if component is still mounted before setting state
          setStatus(response.data.status || 'unknown');
      }
    } catch (error) {
      console.error('Error fetching status:', error.response || error.message);
      if (isMounted.current) {
          setStatus('error');
          // Show toast only once on error, not on every poll failure potentially
          if (status !== 'error') { // Only show toast if status wasn't already error
              toast({
                id: , // Prevent duplicate toasts
                title: 'Error fetching status',
                description: `Could not get status for ${serviceName}: ${error.response?.data?.error || error.message}`,
                status: 'error',
                duration: 5000,
                isClosable: true,
              });
          }
      }
    }
  }, [serviceName, isActionLoading, toast, status]); // status added to prevent redundant error toasts

  // Fetch status on initial mount
  useEffect(() => {
    isMounted.current = true;
    fetchStatus();

    // Cleanup function to set isMounted to false when component unmounts
    return () => {
      isMounted.current = false;
    };
  }, [fetchStatus]); // Run only once on mount

  // Use Chakra's interval hook for polling
  useInterval(fetchStatus, status === 'loading' || isActionLoading ? null : 5000); // Poll every 5s unless an action is happening

  // Handler for start/stop actions
  const handleControl = async (action) => {
    if (!isMounted.current) return; // Prevent action if component unmounted

    setIsActionLoading(true);
    setStatus('loading'); // Indicate action in progress

    const actionVerb = action === 'start' ? 'Starting' : 'Stopping';
    const actionFunc = action === 'start' ? startService : stopService;

    try {
      const response = await actionFunc(serviceName);
      if (isMounted.current) {
        setStatus(response.data.status || 'unknown');
        toast({
          id: ,
          title: `Service  requested`,
          description: response.data.message || `${actionVerb} request sent.`,
          status: 'success',
          duration: 3000,
          isClosable: true,
        });
      }
    } catch (error) {
      console.error(`Error ing service:`, error.response || error.message);
      if (isMounted.current) {
        setStatus('error'); // Set status to error on failure
        toast({
          id: ,
          title: `Failed to  service`,
          description: error.response?.data?.error || error.message,
          status: 'error',
          duration: 5000,
          isClosable: true,
        });
        // Fetch status again after error to get actual state
        fetchStatus();
      }
    } finally {
        // Short delay before re-enabling buttons to allow status to potentially update
        if (isMounted.current) {
            setTimeout(() => setIsActionLoading(false), 1000);
        }
    }
  };

  // Helper to determine badge color based on status
  const getStatusColorScheme = () => {
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

  const isStartDisabled = isActionLoading || status === 'running' || status === 'loading' || status === 'error' || status === 'not_found';
  const isStopDisabled = isActionLoading || status !== 'running' || status === 'loading';

  return (
    <Box p={5} borderWidth="1px" borderRadius="lg" shadow="md">
      <VStack spacing={4} align="stretch">
        <HStack justify="space-between">
          <Heading size="md">{title}</Heading>
          {status === 'loading' && !isActionLoading ? (
              <Spinner size="sm" />
          ) : (
              <Badge fontSize="0.9em" px={3} py={1} borderRadius="full" colorScheme={getStatusColorScheme()}>
                  {status}
              </Badge>
          )}
        </HStack>
        <HStack mt={2} justify="center">
          <Button
            colorScheme="green"
            onClick={() => handleControl('start')}
            isLoading={isActionLoading && status === 'loading'} // Show spinner only during direct action
            isDisabled={isStartDisabled}
            minW="100px"
          >
            Start
          </Button>
          <Button
            colorScheme="red"
            onClick={() => handleControl('stop')}
            isLoading={isActionLoading && status === 'loading'} // Show spinner only during direct action
            isDisabled={isStopDisabled}
            minW="100px"
          >
            Stop
          </Button>
        </HStack>
      </VStack>
    </Box>
  );
}

export default ServiceControl;

