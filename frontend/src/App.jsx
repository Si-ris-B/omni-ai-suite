// File: frontend/src/App.jsx
import React from 'react';
// Import necessary Chakra components and the default system
import {
    ChakraProvider,
    Box,
    Heading,
    VStack,
    Text,
    Separator, // <-- Changed from Divider to Separator
    defaultSystem // Import the default Chakra system for v3+
} from '@chakra-ui/react';
// Import your custom control component
import ServiceControl from './features/control/ServiceControl'; // Verify path is correct

// --- How to Customize Theme in Chakra UI v3+ (If needed later) ---
// 1. Import `createSystem` and `defineConfig` from '@chakra-ui/react'
// 2. Define your config: const config = defineConfig({ theme: { tokens: { colors: { brand: { 500: { value: "#ff0000" }}}}}});
// 3. Create your system: export const customSystem = createSystem(defaultSystem, config);
// 4. Pass `customSystem` to the `value` prop of ChakraProvider below instead of `defaultSystem`.
// --- End Customization Note ---

function App() {
    // Console log to confirm App component execution in browser dev tools
    console.log("[App.jsx] Rendering App component...");

    return (
        // Wrap the entire application in ChakraProvider
        // Provide the Chakra system (using defaultSystem here) via the `value` prop.
        <ChakraProvider value={defaultSystem}>
            {/* Basic page layout styling */}
            <Box p={{ base: 4, md: 8 }} minH="100vh" bg="gray.100"> {/* Light gray background */}
                {/* Content wrapper with max width, centered, background, padding, rounded corners, shadow */}
                <Box maxWidth="container.md" mx="auto" bg="white" p={6} borderRadius="xl" shadow="lg">
                    <VStack spacing={6} align="stretch">
                        {/* Main Application Title */}
                        <Heading as="h1" textAlign="center" size="xl" mb={4} color="teal.700">
                            OmniCore AI Platform
                            <Text as="span" fontSize="lg" fontWeight="medium" color="gray.500"> - PoC Control Panel</Text>
                        </Heading>

                        {/* Service Control Section */}
                        <ServiceControl serviceName="stt" title="Speech-to-Text (STT) Service" />

                        {/* Use the Separator component as per the provided docs */}
                        <Separator my={6} borderColor="gray.300"/>

                        {/* Placeholder for other features */}
                        <Box p={5} borderWidth="1px" borderColor="gray.200" borderRadius="lg" bg="gray.50">
                            <Heading size="md" mb={3} color="gray.600">Future Features Area</Heading>
                            <Text color="gray.700">TTS Control, Diary, Subtitle Tools, Image Recognition modules, etc., will appear here.</Text>
                        </Box>

                    </VStack>
                </Box>
            </Box>
        </ChakraProvider>
    );
}

// Export the App component as the default export
export default App;