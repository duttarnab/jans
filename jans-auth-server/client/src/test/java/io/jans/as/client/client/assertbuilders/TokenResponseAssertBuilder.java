package io.jans.as.client.client.assertbuilders;

import io.jans.as.client.TokenResponse;
import io.jans.as.client.client.AssertBuilder;
import io.jans.as.model.token.TokenErrorResponseType;

import static org.testng.Assert.assertEquals;
import static org.testng.Assert.assertNotNull;

public class TokenResponseAssertBuilder extends BaseAssertBuilder {

    private TokenResponse response;
    private int status = 200;
    private boolean notNullRefreshToken;
    private boolean notNullIdToken;
    private TokenErrorResponseType errorResponseType;

    public TokenResponseAssertBuilder(TokenResponse response) {
        this.response = response;
        this.status = 200;
        this.notNullIdToken = false;
        this.notNullRefreshToken = false;
    }

    public TokenResponseAssertBuilder status(int status) {
        this.status = status;
        return this;
    }

    public TokenResponseAssertBuilder notNullRefreshToken() {
        this.notNullRefreshToken = true;
        return this;
    }

    public TokenResponseAssertBuilder notNullIdToken() {
        this.notNullIdToken = true;
        return this;
    }

    public TokenResponseAssertBuilder errorResponseType(TokenErrorResponseType errorResponseType) {
        this.errorResponseType = errorResponseType;
        return this;
    }

    @Override
    public void checkAsserts() {
        assertNotNull(response, "TokenResponse is null");
        if (status == 200 || status == 201) {
            assertEquals(response.getStatus(), status, "Unexpected response code: " + response.getStatus());
            assertNotNull(response.getEntity(), "The entity is null");
            assertNotNull(response.getAccessToken(), "The access token is null");
            assertNotNull(response.getExpiresIn(), "The expires in value is null");
            assertNotNull(response.getTokenType(), "The token type is null");
            if (notNullIdToken) {
                assertNotNull(response.getIdToken(), "The id token is null");
            }
            if (notNullRefreshToken) {
                assertNotNull(response.getRefreshToken(), "The refresh token is null");
            }
        } else {
            assertEquals(response.getStatus(), status, "Unexpected HTTP status response: " + response.getEntity());
            assertNotNull(response.getEntity(), "The entity is null");
            if (errorResponseType != null) {
                assertEquals(response.getErrorType(), errorResponseType, "Unexpected error type, should be " + errorResponseType.getParameter());
            }
            assertNotNull(response.getErrorDescription());
        }
    }
}
