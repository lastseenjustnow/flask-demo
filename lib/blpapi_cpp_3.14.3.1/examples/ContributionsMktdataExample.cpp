/* Copyright 2012. Bloomberg Finance L.P.
 *
 * Permission is hereby granted, free of charge, to any person obtaining a copy
 * of this software and associated documentation files (the "Software"), to
 * deal in the Software without restriction, including without limitation the
 * rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
 * sell copies of the Software, and to permit persons to whom the Software is
 * furnished to do so, subject to the following conditions:  The above
 * copyright notice and this permission notice shall be included in all copies
 * or substantial portions of the Software.
 *
 * THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
 * IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
 * FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
 * AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
 * LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
 * FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS
 * IN THE SOFTWARE.
 */
#include <blpapi_topiclist.h>
#include <blpapi_providersession.h>
#include <blpapi_eventdispatcher.h>

#include <blpapi_event.h>
#include <blpapi_message.h>
#include <blpapi_element.h>
#include <blpapi_name.h>
#include <blpapi_defs.h>
#include <blpapi_exception.h>
#include <blpapi_topic.h>
#include <blpapi_eventformatter.h>
#include <blpapi_tlsoptions.h>
#include <blpapi_zfputil.h>

#include <ctime>
#include <iostream>
#include <fstream>
#include <iterator>
#include <list>
#include <map>
#include <string>

#include "BlpThreadUtil.h"

using namespace BloombergLP;
using namespace blpapi;

namespace {
    Name TOKEN_SUCCESS("TokenGenerationSuccess");
    Name TOKEN_FAILURE("TokenGenerationFailure");
    Name AUTHORIZATION_SUCCESS("AuthorizationSuccess");
    Name TOKEN("token");
    Name MARKET_DATA("MarketData");
    Name SESSION_TERMINATED("SessionTerminated");

    const char *AUTH_USER        = "AuthenticationType=OS_LOGON";
    const char *AUTH_APP_PREFIX  = "AuthenticationMode=APPLICATION_ONLY;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
    const char* AUTH_USER_APP_PREFIX = "AuthenticationMode=USER_AND_APPLICATION;AuthenticationType=OS_LOGON;ApplicationAuthenticationType=APPNAME_AND_KEY;ApplicationName=";
    const char *AUTH_DIR_PREFIX  = "AuthenticationType=DIRECTORY_SERVICE;DirSvcPropertyName=";

    const char *AUTH_OPTION_NONE = "none";
    const char *AUTH_OPTION_USER = "user";
    const char *AUTH_OPTION_APP  = "app=";
    const char* AUTH_OPTION_USER_APP  = "userapp=";
    const char *AUTH_OPTION_DIR  = "dir=";

    volatile bool g_running = true;

    Mutex g_lock;

    enum AuthorizationStatus {
        WAITING,
        AUTHORIZED,
        FAILED
    };

    std::map<CorrelationId, AuthorizationStatus> g_authorizationStatus;

    int readFromFile(const std::string& filename, std::string& buffer)
    {
        std::ifstream in(filename.c_str(),
                         std::ios::in | std::ios::binary | std::ios::ate);
        if (in) {
            buffer.resize(in.tellg());
            in.seekg(0, std::ios::beg);
            in.read(&buffer[0], buffer.size());
        }

        if (in.fail()) {
            std::cerr << "Failed to read file from " << filename << std::endl;
            return 1;
        }

        std::cout << "Read " << buffer.size() << " bytes from "
                  << filename << std::endl;
        return 0;
    }
}

class MyStream {
    std::string d_id;
    Topic d_topic;

public:
    MyStream() : d_id("") {}
    MyStream(std::string const& id) : d_id(id) {}
    void setTopic(Topic const& topic) { d_topic = topic; }
    std::string const& getId() { return d_id; }
    Topic const& getTopic() { return d_topic; }
};

typedef std::list<MyStream*> MyStreams;

class MyEventHandler : public ProviderEventHandler {
public:
    bool processEvent(const Event& event, ProviderSession* session);
};

bool MyEventHandler::processEvent(const Event& event, ProviderSession* session) {
    MessageIterator iter(event);
    while (iter.next()) {
        Message msg = iter.message();
        MutexGuard guard(&g_lock);
        msg.print(std::cout);
        if (event.eventType() == Event::SESSION_STATUS) {
            if (msg.messageType() == SESSION_TERMINATED) {
                g_running = false;
            }
            continue;
        }
        if (g_authorizationStatus.find(msg.correlationId()) != g_authorizationStatus.end()) {
            if (msg.messageType() == AUTHORIZATION_SUCCESS) {
                g_authorizationStatus[msg.correlationId()] = AUTHORIZED;
            }
            else {
                g_authorizationStatus[msg.correlationId()] = FAILED;
            }
        }
    }

    return true;
}

class ContributionsMktdataExample
{
    std::vector<std::string> d_hosts;
    int                      d_port;
    std::string              d_service;
    std::string              d_topic;
    std::string              d_authOptions;

    std::string              d_clientCredentials;
    std::string              d_clientCredentialsPassword;
    std::string              d_trustMaterial;
    bool                     d_readTlsData;

    bool                     d_zfpOverLeasedLine;
    ZfpUtil::Remote          d_remote;

    void printUsage()
    {
        std::cout
            << "Market data contribution." << std::endl
            << "Usage:" << std::endl
            << "\t[-ip   <ipAddress>]  \tserver name or IP (default: localhost)" << std::endl
            << "\t[-p    <tcpPort>]    \tserver port (default: 8194)" << std::endl
            << "\t[-s    <service>]    \tservice name (default: //blp/mpfbapi)" << std::endl
            << "\t[-t    <topic>]      \tservice name (default: /ticker/AUDEUR Curncy)" << std::endl
            << "\t[-auth <option>]     \tauthentication option: user|none|app=<app>|userapp=<app>|dir=<property> (default: user)\n"
            << std::endl
            << "TLS OPTIONS (specify all or none):\n"
               "\t[-tls-client-credentials <file>] \tname a PKCS#12 file to use as a source of client credentials\n"
               "\t[-tls-client-credentials-password <pwd>] \tspecify password for accessing client credentials\n"
               "\t[-tls-trust-material <file>]     \tname a PKCS#7 file to use as a source of trusted certificates\n"
               "\t[-read-certificate-files]        \t(optional) read the TLS files and pass the blobs\n"
            << std::endl
            << "ZFP connections over leased lines (requires TLS options):\n"
            << "\t[-zfp-over-leased-line <port>]       enable ZFP connections over leased lines on the specified port (8194 or 8196)\n"
            << "\t\tWhen this option is enabled, '-ip' and '-p' arguments will be ignored.\n\n";
    }

    bool parseCommandLine(int argc, char **argv)
    {
        for (int i = 1; i < argc; ++i) {
            if (!std::strcmp(argv[i],"-ip") && i + 1 < argc)
                d_hosts.push_back(argv[++i]);
            else if (!std::strcmp(argv[i],"-p") &&  i + 1 < argc)
                d_port = std::atoi(argv[++i]);
            else if (!std::strcmp(argv[i],"-s") &&  i + 1 < argc)
                d_service = argv[++i];
            else if (!std::strcmp(argv[i],"-t") &&  i + 1 < argc)
                d_topic = argv[++i];
            else if (!std::strcmp(argv[i], "-auth") && i + 1 < argc) {
                ++ i;
                if (!std::strcmp(argv[i], AUTH_OPTION_NONE)) {
                    d_authOptions.clear();
                }
                else if (!std::strcmp(argv[i], AUTH_OPTION_USER)) {
                    d_authOptions.assign(AUTH_USER);
                }
                else if (strncmp(argv[i], AUTH_OPTION_APP,
                                 strlen(AUTH_OPTION_APP)) == 0) {
                    d_authOptions.clear();
                    d_authOptions.append(AUTH_APP_PREFIX);
                    d_authOptions.append(argv[i] + strlen(AUTH_OPTION_APP));
                }
                else if (strncmp(argv[i], AUTH_OPTION_USER_APP, strlen(AUTH_OPTION_USER_APP)) == 0) {
                    d_authOptions.clear();
                    d_authOptions.append(AUTH_USER_APP_PREFIX);
                    d_authOptions.append(argv[i] + strlen(AUTH_OPTION_USER_APP));
                }
                else if (strncmp(argv[i], AUTH_OPTION_DIR,
                                 strlen(AUTH_OPTION_DIR)) == 0) {
                    d_authOptions.clear();
                    d_authOptions.append(AUTH_DIR_PREFIX);
                    d_authOptions.append(argv[i] + strlen(AUTH_OPTION_DIR));
                }
            } else if (!std::strcmp(argv[i], "-tls-client-credentials") && i + 1 < argc) {
                d_clientCredentials = argv[++i];
            } else if (!std::strcmp(argv[i], "-tls-client-credentials-password") && i + 1 < argc) {
                d_clientCredentialsPassword = argv[++i];
            } else if (!std::strcmp(argv[i], "-tls-trust-material") && i + 1 < argc) {
                d_trustMaterial = argv[++i];
            } else if (!std::strcmp(argv[i], "-read-certificate-files")) {
                d_readTlsData = true;
            }
            else if (!std::strcmp(argv[i], "-zfp-over-leased-line") && i + 1 < argc) {
                d_zfpOverLeasedLine = true;
                ++i;
                if (!std::strcmp(argv[i], "8194")) {
                    d_remote = ZfpUtil::REMOTE_8194;
                }
                else if (!std::strcmp(argv[i], "8196")) {
                    d_remote = ZfpUtil::REMOTE_8196;
                }
                else {
                    std::cerr << "Invalid ZFP port: " << argv[i] << "\n\n";
                    printUsage();
                    return false;
                }
            } else {
                printUsage();
                return false;
            }
        }

        if (d_hosts.empty()) {
            d_hosts.push_back("localhost");
        }

        return true;
    }

public:

    ContributionsMktdataExample()
        : d_hosts()
        , d_port(8194)
        , d_service("//blp/mpfbapi")
        , d_topic("/ticker/AUDEUR Curncy")
        , d_authOptions(AUTH_USER)
        , d_readTlsData(false)
        , d_zfpOverLeasedLine(false)
    {
    }

    bool authorize(const Service& authService,
                   Identity *providerIdentity,
                   ProviderSession *session,
                   const CorrelationId& cid)
    {
        {
            MutexGuard guard(&g_lock);
            g_authorizationStatus[cid] = WAITING;
        }
        EventQueue tokenEventQueue;
        session->generateToken(CorrelationId(), &tokenEventQueue);
        std::string token;
        Event event = tokenEventQueue.nextEvent();
        if (event.eventType() == Event::TOKEN_STATUS ||
            event.eventType() == Event::REQUEST_STATUS) {
            MessageIterator iter(event);
            while (iter.next()) {
                Message msg = iter.message();
                {
                    MutexGuard guard(&g_lock);
                    msg.print(std::cout);
                }
                if (msg.messageType() == TOKEN_SUCCESS) {
                    token = msg.getElementAsString(TOKEN);
                }
                else if (msg.messageType() == TOKEN_FAILURE) {
                    break;
                }
            }
        }
        if (token.length() == 0) {
            MutexGuard guard(&g_lock);
            std::cout << "Failed to get token" << std::endl;
            return false;
        }

        Request authRequest = authService.createAuthorizationRequest();
        authRequest.set(TOKEN, token.c_str());

        session->sendAuthorizationRequest(
            authRequest,
            providerIdentity,
            cid);

        time_t startTime = time(0);
        const int WAIT_TIME_SECONDS = 10;
        while (true) {
            {
                MutexGuard guard(&g_lock);
                if (WAITING != g_authorizationStatus[cid]) {
                    return AUTHORIZED == g_authorizationStatus[cid];
                }
            }
            time_t endTime = time(0);
            if (endTime - startTime > WAIT_TIME_SECONDS) {
                return false;
            }
            SLEEP(1);
        }
    }

    bool prepareTlsOptions(TlsOptions& tlsOptions)
    {
        if (d_readTlsData) {
            std::string clientCredentials;
            std::string trustMaterial;

            if (readFromFile(d_clientCredentials, clientCredentials)
                || readFromFile(d_trustMaterial, trustMaterial)) {
                // Failed to read from files
                return false;
            }

            tlsOptions = TlsOptions::createFromBlobs(
                clientCredentials.data(),
                clientCredentials.size(),
                d_clientCredentialsPassword.c_str(),
                trustMaterial.data(),
                trustMaterial.size());
        }
        else {
            tlsOptions =
                TlsOptions::createFromFiles(
                d_clientCredentials.c_str(),
                d_clientCredentialsPassword.c_str(),
                d_trustMaterial.c_str());
        }
        return true;
    }

    bool prepareStandardSessionOptions(SessionOptions& sessionOptions)
    {
        for (size_t i = 0; i < d_hosts.size(); ++i) {
            sessionOptions.setServerAddress(d_hosts[i].c_str(), d_port, i);
        }
        sessionOptions.setServerPort(d_port);
        sessionOptions.setAuthenticationOptions(d_authOptions.c_str());
        sessionOptions.setAutoRestartOnDisconnection(true);
        sessionOptions.setNumStartAttempts(d_hosts.size());

        if (d_clientCredentials.size()
            && d_trustMaterial.size()) {

            std::cout << "TlsOptions enabled" << std::endl;
            TlsOptions tlsOptions;

            if (!prepareTlsOptions(tlsOptions)) {
                return false;
            }

            sessionOptions.setTlsOptions(tlsOptions);
        }
        return true;
    }

    bool prepareZfpSessionOptions(SessionOptions& sessionOptions)
    {
        if (d_clientCredentials.empty() || d_trustMaterial.empty()) {
            std::cerr << "ZFP connections require TLS parameters";
            return false;
        }

        std::cout << "Creating a ZFP connection for leased lines." << std::endl;
        TlsOptions tlsOptions;
        if (!prepareTlsOptions(tlsOptions)) {
            return false;
        }
        sessionOptions = ZfpUtil::getZfpOptionsForLeasedLines(
            d_remote, tlsOptions);
        sessionOptions.setAuthenticationOptions(d_authOptions.c_str());
        return true;
    }

    bool prepareSessionOptions(SessionOptions& sessionOptions)
    {
        if (d_zfpOverLeasedLine) {
            if (!prepareZfpSessionOptions(sessionOptions)) {
                return false;
            }
        }
        else {
            if (!prepareStandardSessionOptions(sessionOptions)) {
                return false;
            }
        }
        return true;
    }

    void run(int argc, char **argv)
    {
        if (!parseCommandLine(argc, argv))
            return;

        SessionOptions sessionOptions;
        if (!prepareSessionOptions(sessionOptions)) {
            return;
        }

        MyEventHandler myEventHandler;
        ProviderSession session(sessionOptions, &myEventHandler, 0);

        std::cout << "Connecting to port " << d_port
                  << " on ";
        std::copy(d_hosts.begin(), d_hosts.end(), std::ostream_iterator<std::string>(std::cout, " "));
        std::cout << std::endl;

        if (!session.start()) {
            std::cerr <<"Failed to start session." << std::endl;
            return;
        }

        Identity providerIdentity;
        if (!d_authOptions.empty()) {
            providerIdentity = session.createIdentity();
            bool isAuthorized = false;
            const char* authServiceName = "//blp/apiauth";
            if (session.openService(authServiceName)) {
                Service authService = session.getService(authServiceName);
                isAuthorized = authorize(authService, &providerIdentity,
                        &session, CorrelationId((void *)"auth"));
            }
            if (!isAuthorized) {
                std::cerr << "No authorization" << std::endl;
                return;
            }
        }

        TopicList topicList;
        topicList.add((d_service + d_topic).c_str(),
            CorrelationId(new MyStream(d_topic)));

        session.createTopics(
            &topicList,
            ProviderSession::AUTO_REGISTER_SERVICES,
            providerIdentity);
        // createTopics() is synchronous, topicList will be updated
        // with the results of topic creation (resolution will happen
        // under the covers)

        MyStreams myStreams;

        for (size_t i = 0; i < topicList.size(); ++i) {
            MyStream *stream = reinterpret_cast<MyStream*>(
                topicList.correlationIdAt(i).asPointer());
            int resolutionStatus = topicList.statusAt(i);
            if (resolutionStatus == TopicList::CREATED) {
                Topic topic = session.getTopic(topicList.messageAt(i));
                stream->setTopic(topic);
                myStreams.push_back(stream);
            }
            else {
                std::cout
                    << "Stream '"
                    << stream->getId()
                    << "': topic not resolved, status = "
                    << resolutionStatus
                    << std::endl;
            }
        }

        Service service = session.getService(d_service.c_str());

        // Now we will start publishing
        int value = 1;
        while (myStreams.size() > 0 && g_running) {
            Event event = service.createPublishEvent();
            EventFormatter eventFormatter(event);

            for (MyStreams::iterator iter = myStreams.begin();
                 iter != myStreams.end(); ++iter)
            {
                eventFormatter.appendMessage(MARKET_DATA, (*iter)->getTopic());
                eventFormatter.setElement("BID", 0.5 * ++value);
                eventFormatter.setElement("ASK", value);
            }

            MessageIterator iter(event);
            while (iter.next()) {
                Message msg = iter.message();
                msg.print(std::cout);
            }

            session.publish(event);
            SLEEP(10);
        }

        session.stop();
    }
};

int main(int argc, char **argv)
{
    std::cout << "ContributionsMktdataExample" << std::endl;
    ContributionsMktdataExample example;
    try {
        example.run(argc, argv);
    } catch (Exception &e) {
        std::cerr << "Library Exception!!! " << e.description() << std::endl;
    }
    // wait for enter key to exit application
    std::cout << "Press ENTER to quit" << std::endl;
    char dummy[2];
    std::cin.getline(dummy, 2);
    return 0;
}
