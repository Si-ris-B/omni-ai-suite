import React from 'react';
import {
  ChakraProvider,
  Box,
  Heading,
  VStack,
  Divider,
  extendTheme,
} from '@chakra-ui/react';
import ServiceControl from './features/control/ServiceControl'; // Adjust path if needed

// Optional: Extend Chakra theme if desired
const theme = extendTheme({
  // Add custom theme settings here
});

function App() {
  return (
    <ChakraProvider theme={theme}>
      <Box p={5} maxWidth="container.md" mx="auto">
        {' '}
        {/* Center content */}
        <VStack spacing={6} align="stretch">
          <Heading textAlign="center" size="xl" mb={4}>
            OmniCore AI Platform - PoC
          </Heading>

          {/* Service Control Section */}
          <ServiceControl serviceName="stt" title="Speech-to-Text Service" />

          <Divider />

          {/* Placeholder for other features */}
          <Box p={5} borderWidth="1px" borderRadius="lg" bg="gray.50">
            <Heading size="md" mb={3}>
              Other Features Area
            </Heading>
            <Text>Future components (TTS, Diary, etc.) will go here.</Text>
          </Box>
        </VStack>
      </Box>
    </ChakraProvider>
  );
}

export default App;
